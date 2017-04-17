#- protocolo textual:
# ####  -- JOIN [apelido] 
#   * junta-se ao grupo de conversação 
#   -- JOINACK [apelido] 
#   * resposta ao JOIN para possibilitar a manutenção da lista de usuários ativos
#   -- MSG [apelido] "texto"
#   * mensagem enviada a todos os membros do grupo pelo IP 225.1.2.3 e porta 6789 
#   -- MSGIDV FROM [apelido] TO [apelido] "texto" 
#   * mensagem enviada a um membro do grupo para ser recebida na porta 6799
#   -- LISTFILES [apelido] 
#   * solicitação de listagem de arquivos para um usuário 
#   -- FILES [arq1, arq2, arqN] 
#   * resposta para o LISTFILES
#   -- DOWNFILE [apelido] filename 
#   * solicita arquivo do servidor. 
#   -- DOWNINFO [filename, size, IP, PORTA] 
#   * resposta com informações sobre o arquivo e conexão TCP. 
# ####  -- LEAVE [apelido] * deixa o grupo de conversação

import socket
import sys
import os
import struct
from threading import Thread
#multicast comunication class

class mc(object):
    def __init__(self):
        self.users = {}
        self.PORT = 6789
        #address to bind
        self.address = '225.1.2.3'
        #group adress + port
        self.group_adp = (self.address, self.PORT)
        #local socket
        self.local_PORT = 6799
        self.localaddress = ''
        self.local_adp = ('0.0.0.0', self.local_PORT)
        #creating sockets
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp.bind(self.group_adp)
        mreq = struct.pack("4sl", socket.inet_aton(self.address), socket.INADDR_ANY)
        self.udp.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.local_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.nickname = ''
        self.reserved_receive = {"JOIN": self.send_ack, "MSG": self.receive_msg, "LEAVE": self.receive_leave}
        self.reserved_receive_local= {"JOINACK": self.receive_ack, "MSGIDV": self.receive_msgidv, "LISTFILES": self.send_files, "FILES": self.receive_files, "DOWNFILE": self.send_downinfo, "DOWNINFO": self.downinfo}
        self.reserved = {"\downfile": self.send_downfile, "sair": self.quit, "\leave": self.quit, "\list": self.list_users, "\private": self.send_msgidv, "\lf": self.send_list_files}
        
        self.files = {} ###### colocar aqui os arquivos que devem ser enviados
        self.local_udp.bind(self.local_adp)
        self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def receive_files(self, *l):
        recebido = l[1].replace("FILES ",'')
        print("Arquivos recebidos do listfile: {}".format(recebido))


    def downinfo(self,*l):

        raw = l[1].replace("[","").replace(']','')
        raw = raw.split(", ")
        name = raw[0].replace("DOWNINFO ",'') 
        IP = raw[2]
        porta = raw[3]
        tocon = (IP, int(porta))
        self.tcp.connect(tocon)
        fo = open("download-"+name, 'wb')
        print("Criando arquivo")
        l = self.tcp.recv(1024)
        while (l):
            fo.write(l)
            l.self.tcp.recv(1024)
        fo.close()
        l.self.tcp.close()

    #envia um downinfo como resposta e aguarda conexão
    ## {file1: size, file2: size2}
    def send_downinfo(self, *l):
        name = l[1].rpartition('] ')[2]
        size = self.files[name]
        myaddress = (self.list_users(self.nickname)[0], 6790)
        IP = myaddress[0]
        porta = myaddress[1]
        self.tcp.bind(myaddress)
        enviar = "DOWNINFO [{0}, {1}, {2}, {3}]".format(name, size, IP, porta) 
        self.local_udp.sendto(enviar.encode(), (l[0][0],self.local_PORT))
        self.tcp.listen(1)
        con, cliente = self.tcp.accept()
        f = open('./'+name, 'rb')
        stream = f.read(1024)
        while (stream):
            con.send(stream)
            stream = f.read(1024)
        con.shutdown(socket.SHUT_WR)
        f.close()
        con.close()

    def send_downfile(self, *l):
        try:
            inp = input("Digite o nome do usuário que deseja baixar arquivo: ")
            filename = input("Digite o nome do arquivo que deseja baixar: ")
            addr = self.list_users(inp)
            print("O endereço obtido é: {}".format(addr))
            enviar = "DOWNFILE [{0}] {1}".format(self.nickname, filename)
            self.local_udp.sendto(enviar.encode(), (addr[0], self.local_PORT))
        except Exception as e:
            print(e) 
            print("Ocorreu algum erro para idêntificar o usuário ou enviar a solicitação")

    def send_list_files(self):
        try:
            inp = input("Digite o nome do usuário que deseja listar arquivos: ")
            addr = self.list_users(inp)
            print("endereco obtido: {}".format(addr))
            enviar = "LISTFILES [{}]".format(self.nickname)
            self.local_udp.sendto(enviar.encode(), (addr[0], self.local_PORT))
        except Exception as e:
            print(e) 
            print("Ocorreu algum erro para idêntificar o usuário digitado")

    def receive_msgidv(self, *l):
        msg = list(l[1].partition('[')[2].partition(']'))
        msg[2] = msg[2].rpartition('] ')[-1]
        print("PRIVADA DE {0}: {1}".format(msg[0],msg[-1]))

    def send_msgidv(self):
        self.list_users()
        addr = ''
        msg = ''
        try:
            inp = input("Digite o nome do usuário que deseja mandar msg privada: ")
            addr = self.list_users(inp)
            print("O endereço para enviar é: {}\nDigite \\noprivate para sair do modo de msg privada".format(addr))
            while inp != "\\noprivate":
                inp = input()
                msg = "privada: " + inp
                enviar = "MSGIDV FROM [{0}] TO [{1}] {2}".format(self.nickname, inp, msg) 
                self.local_udp.sendto(enviar.encode(), (addr[0], self.local_PORT))
        except Exception as e:
            print(e) 
            print("Ocorreu algum erro para idêntificar o usuário digitado")


    def config(self):
        testing = True
        while True:
            try:
                self.nickname = str(input("Digite seu apelido: "))             
                for dirpath, dirnames, filenames in os.walk('./', topdown=True):
                    print (filenames)
                    for f in filenames:
                        self.files[f] = os.path.getsize(f)
                    break #para não ser recursivo
                return True
            except Exception as e:
                print(e) 
                print("Apelido inválido ou pasta vazia!\nDigite um formato string ou verifique se sua pasta contém arquivos")


    def send_group(self, enviar):
        self.udp.sendto(enviar, self.group_adp)

    def user_input(self):
        self.config()
        self.udp.sendto('JOIN [{}]'.format(self.nickname).encode(), self.group_adp)
        msg = ''
        tag = ''
        while True:
            msg = input()		
            try:
                self.reserved[msg]()
            except Exception as e:
               # print(e) 
                tag = "MSG"
                enviar = "{0} [{1}] {2}".format(tag, str(self.nickname), str(msg),)
                self.send_group(enviar.encode())
        exit()

####### ver como envia arquivo
    def send_files(self,*l):
        addr = l[0]
        enviar = "{0} {1}".format("FILES",list(self.files.keys()))
        enviar = enviar.encode()
        self.local_udp.sendto(enviar, (addr[0],self.local_PORT))

    def quit(self,*l):
        enviar = "LEAVE [{}]".format(self.nickname)
        self.udp.sendto(enviar.encode(), self.group_adp)
        self.udp.close()
        self.local_udp.close()
        sys.exit()
        return ('LEAVE','')

    def send_ack(self, *l):
        addr = l[0]
        msg = l[1].partition('[')[-1]
        msg = msg.replace(']','')
        print("{0} entrou no grupo".format(msg))
        enviar = "{0} [{1}]".format("JOINACK",self.nickname)
        enviar = enviar.encode()
        a = self.local_udp.sendto(enviar, (addr[0],self.local_PORT))


    def receive(self): 
        while True:
            msg, sender_addr = self.udp.recvfrom(1024) #tamanho do buffer 1024
            msg = msg.decode()
            print("\n---msg: {}\n".format(msg))
            #func = self.reserved[msg.split(' ')[0]]
            #func(sender_addr,msg)
            #Thread(target=func, args=(sender_addr, msg)).start()
            try:
                #arg0 = endereco, arg1 = mensagem
                self.reserved_receive[msg.split(' ')[0]](sender_addr,msg)

                #Thread.start_new_thread(self.reserved[msg.split(' ')[0]], args=(sender_addr, msg))
            except Exception as e:
                print(e) 
                self.padrao_erro()

    def receive_local(self):
        while True:
            msg, sender_addr = self.local_udp.recvfrom(1024) #tamanho do buffer 1024
            msg = msg.decode()
            print("\n---LOCAL: {}\n".format(msg))
            #func = self.reserved[msg.split(' ')[0]]
            #func(sender_addr,msg)
            #Thread(target=func, args=(sender_addr, msg)).start()
            try:
                #arg0 = endereco, arg1 = mensagem
                Thread(target=self.reserved_receive_local[msg.split(' ')[0]], args=([sender_addr, msg]))
                ####self.reserved_receive_local[msg.split(' ')[0]](sender_addr,msg)

            except Exception as e:
                print(e) 
                self.padrao_erro()
            ########self.reserved_receive_local[msg.split(' ')[0]](sender_addr,msg)


    def padrao_erro(self, *l):
        print("Mensagem sem padrão foi recebida: {0}\n".format(l))
                
    def receive_msg(self, *l):
        
        exibir = list(l[1].rpartition('['))
        exibir = exibir[2].rpartition(']')
        print("{0}: {1}".format(exibir[0],exibir[2]))

    def receive_ack(self, *l):
        #[1] = nickname [0] = ip
        self.users[l[1].partition('[')[-1][:-1]] = l[0]

    def receive_leave(self, *l):
        usuario = l[1].partition('[')[-1][-1]
        self.users.pop[usuario]
        print("{} saiu".format(usuario))

    def list_users(self, *l):
        try:
            return self.users[l[0]]
        except Exception as e:
            print(e) 
            print("usuarios online: {}".format(list(self.users.keys())))

        
chat = mc()

Thread(target=chat.user_input).start()#chat.user_input)
Thread(target=chat.receive).start()
Thread(target=chat.receive_local).start()
#Thread.start_new_thread(chat.receive_ack)


