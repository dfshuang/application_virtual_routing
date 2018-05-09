import socket
import os
from tools import *
import time
import multiprocessing



#TODO 和路由信息有关的，登录获取已上线的ip, 
#随机重组(保证每个路由器只有两个接口，由Tractor分配)
"""


协议详情：
    Peer与Tractor的通信：
    1.Peer登陆后向Tractor提交自己的所有文件信息
        #Peer: (HAVE MESSIZE MSG)
        #Tractor: (HAVE OK)
      登录后向控制器注册，由控制器随机分配路由信息
         
    2.Peer向Tractor请求所有的文件
        #Peer: (SHOW)
        #Tractor (SHOW OK msgSize )FileName, FileName...
    3.Peer向Tractor请求文件的ip列表
        #Peer： (GET FileName)
        #Tractor: (GET OK msgSize) ip,ip,ip...
    4.路由请求：
        peer: ROUTE destip
        Tractor: ROUTE OK MESSIZE
                 addr[0], ... , destip
    5.传递数据：
        peer: TRANS dest msgsize
              infor
        another peer: TRANS OK, not print(info)
        last peer: TRANS OK, print(info)

        #升级用。先不考虑这些吧。
        #Tractor：GET FAILED
    
    Peer与Peer的通信：
    
    Peer_Client:(GET FileName offset N)
    Peer_Server:(GET OK TotalBytes offset) data


"""


'''
    str --> list  string.split(' ')
    list --> str  string.join(list)  

    list = ['a', 'b']
    ','.join(list) --> 'a,b'
'''


class Router():
    def __init__(self, tractorAddr='localhost', tractorPort=5555, peerPort=6666, MaxConnect=10):
        """
            初始化函数，会向服务器发送自己的资源信息
            tractorAddr = 'localhost':指定Tractor的地址
            tractorPort = 5555：指定tractor的端口
            peerPort = 6666：用于其他peer连接的端口
            MaxConnect = 10：最大连接数。即最多被这么多个对等方请求文件

            # Peer: HAVE MESSIZE MSG
            # Tractor: HAVE OK
        """
        #获取本地目录
        print("hello")
        self.dir = os.getcwd()
        print("now you are at " + self.dir)
        self.Tsock = socket.socket()
        self.Tsock.connect((tractorAddr, tractorPort))

        #发送当前目录文件名给Tractor
        send_data = ','.join(os.listdir(self.dir))
        print("current directory has file: \n  " + send_data)
        send_data = send_data.encode('utf8')
        msg_size = len(send_data)
        header = "HAVE " + str(msg_size) + " "
        print(header)
        header = header.encode('utf8')
        padding = [32 for x in range(HEADER_SIZE - len(header))]
        self.Tsock.sendall(header)
        self.Tsock.sendall(bytes(padding))
        self.Tsock.sendall(send_data)

        #接收回复
        header = getHeader(self.Tsock)
        if header[:7] == 'HAVE OK':
            print(header[:7])
        else:
            print('ERROR INITIALIZATION')


        self.ipaddr = '127.0.0.1'
        # 并行？一直等待？
        # 等待Peer的连接
        self.Psock = socket.socket()
        self.Psock.bind((self.ipaddr, peerPort))
        self.Psock.listen(MaxConnect)
        multiprocessing.Process(target=self.waitForPeer).start()



    def getFile(self, fileName):
        """
            获取文件，从跟踪器上获取所有的资源ip，然后连接上获取文件。
        """

        # 传给tractor, 发送get filename请求
        header = "GET " + fileName
        header = header.encode('utf8')
        # 32 --> ' ' ascii
        padding = [32 for x in range(HEADER_SIZE - len(header))]

        self.Tsock.sendall(header)
        self.Tsock.sendall(bytes(padding))

        # 获取有相关文件的peer信息
        header = getHeader(self.Tsock)
        headerSplit = header.split(' ')
        if headerSplit[1] == 'OK':
            print(headerSplit[0] + ' ' + headerSplit[1])
            msgSize = int(headerSplit[2])

            data = [0 for x in range(msgSize)]
            readNbytes(self.Tsock, data, msgSize)

            # 获取相应的文件的其余对等方ip地址
            # msg为字符串
            msg = bytes(data).decode('utf8')
            print("ip list is: " + msg)
            ipList = msg.split(',')

            # 告诉peer会将文件分成几份，然后你的编号是多少即可。
            for i in range(len(ipList)):
                ip = ipList[i]
                p = multiprocessing.Process(
                    target=self.handleGetFile, args=(fileName, ip, i, len(ipList), ))
                p.start()
            p.join()

            print("downloading...")
            # 把文件连在一起, 先输入新建的文件名
            newFileName = str(input("Please input new name of the file: "))
            with open(newFileName, 'ab') as fw:
                for i in range(len(ipList)):
                    #读取分片文件 
                    with open(fileName + '_temp' + str(i), 'rb') as fr:
                        for line in fr.readlines():
                            fw.write(line)
            print("download successfully!")
        else:
            print('ERROR TO GET FILE')

        pass

    def handleGetFile(self, fileName, ip, i, n):
        """
            从某个Ip获取一定大小的文件
            i偏移量
            n总数
            协议描述：
            Peer_Client:GET FileName offset N
            Peer_Server:GET OK TotalBytes offset data
        """
        # 保存到一个临时文件。
        Csock = socket.socket()
        #socket.gethostbyaddr(ip)
        Csock.connect(('localhost', 6666))

        # 新建一个套接字，连接peer的Psock

        header = ('GET ' + fileName + ' ' + str(i) +
                  ' ' + str(n)).encode('utf8')
        padding = [32 for x in range(HEADER_SIZE - len(header))]
        Csock.sendall(header)
        Csock.sendall(bytes(padding))

        # 对待第一个要慎重。

        header = getHeader(Csock)
        headerList = header.split(' ')

        totalBytes = int(headerList[2])

        # 计算需要传递多少字节的算法。前面的整除，最后的一次性传完。
        expected = totalBytes//n
        if i == n - 1:
            expected += totalBytes % n

        #从另一个peer接收的对应的文件数据
        data = [0 for x in range(expected)]
        readNbytes(Csock, data, expected)

        #将数据存储在本地
        with open(fileName + '_temp' + str(i), 'wb') as temp:
            temp.write(bytes(data))
            pass

    def waitForPeer(self):
        while True:

            conn, addr = self.Psock.accept()

            p = multiprocessing.Process(target=self.process_info, args=(conn, ))

            p.start()

        pass

    def process_info(self, conn):
        """
            peer传输文件给另一个peer
            从某个Ip获取一定大小的文件
            i偏移量
            n总数
            协议描述：
            Peer_Client:GET FileName offset N
            Peer_Server:GET OK TotalBytes offset data
        """

        header = getHeader(conn)
        headerSplit = header.split(' ')

        if headerSplit[0] == 'GET':
            #处理客户端header
            filename = headerSplit[1]
            fileoffset = int(headerSplit[2]) #第几个peer
            fileall = int(headerSplit[3])    #总的拥有相应文件的peer数  
        
            if os.path.exists(filename):
                filesize = os.path.getsize(filename)  #要传输的文件的总大小
                first = int(fileoffset/fileall * filesize)  #要传输的文件首地址，偏移量
                last = int((fileoffset+1) / fileall * filesize - 1)  #要传输的文件尾地址
                if last > filesize:
                    last = filesize - 1

                #发送服务器header
                header = ('GET OK ' + str(filesize) + ' ' + str(fileoffset)).encode('utf8')
                padding = [32 for x in range(HEADER_SIZE - len(header))]
                conn.sendall(header)
                conn.sendall(bytes(padding))

                wantTranSize = last - first + 1  #要传输的文件的传输部分的大小
                with open(filename, 'rb') as fr:
                    print("sending " + filename + " ...")
                    fr.seek(first, 0)                   
                    strToTran = fr.read(wantTranSize)
                    conn.sendall(strToTran)
                    print("sending successfully!")
                    print(">>> ")
                
            else:
                print("ERROR, can't not find the file")

        elif headerSplit[0] == 'TRANS':
            destIp = headerSplit[1]
            msgsize = int(headerSplit[2])
            info = [0 for x in range(msgsize)]
            readNbytes(conn, info, msgsize)

            info_send = bytes(info.decode('utf8'))
            self.transmiss(destIp, info_send)

        else:
            print("ERROR, not get or trans")
        # 发送对应文件内容
        
    # 展示所有的可下载文件
    def show(self):
        """
            客户端程序，发送请求

            client: SHOW

            Tractor:SHOW OK MESSSIZE
                    fileName, fileName...
        """
        header = 'SHOW'.encode('utf8')
        print(header)
        padding = [32 for x in range(HEADER_SIZE - len(header))]
        self.Tsock.sendall(header)
        self.Tsock.sendall(bytes(padding))

        #获取头信息show ok ....
        gethead = getHeader(self.Tsock)      
        msgSize = int(gethead[8:])
        data = [0 for x in range(msgSize)]
        readNbytes(self.Tsock, data, msgSize)
        print(''.join(bytes(data).decode()))
        pass

    def askRoute(self, dest):
        """
            dest: str
            return: a list of ip 

            向控制器请求路由路径信息
            Route: ROUTE destip
            Controller: ROUTE OK MESSIZE
                 addr[0], ... , destip
        """
        #发送路径信息请求
        header = ('ROUTE ' + dest).encode('utf8')
        print(header)
        padding = [32 for x in range(HEADER_SIZE - len(header))]
        self.Tsock.sendall(header)
        self.Tsock.sendall(bytes(padding))

        #接收路径信息
        gethead = getHeader(self.Tsock)      
        msgSize = int(gethead[9:])
        data = [0 for x in range(msgSize)]
        readNbytes(self.Tsock, data, msgSize)
        route_infor = ''.join(bytes(data).decode())
        route_infor.split(',')
        print(route_infor)

        return route_infor


    def transmiss(self, dest, info):
        """
            dest: 下一跳地址，若是自己，则已到达目的地
            infor: str

            根据路由信息提供的路径传输数据

            找到自己的ip地址，然后传给下一跳，若是最后的地址，则不用再传输
        """
        routei = self.askRoute(dest)

        if self.ipaddr in routei:
            if len(routei) == 1:
                #到终点了
                print(info)
            else:
                #打包传输给下一跳routei[1]
                #TRANS dest size
                #info
                
                Csock = socket.socket()
                #socket.gethostbyaddr(ip), 'localhost'
                Csock.connect((socket.gethostbyaddr(routei[1]), 6666))

                # 新建一个套接字，连接peer的Psock
                #发送头
                header = ('TRANS ' + routei[1] + ' ' + len(info)).encode('utf8')
                padding = [32 for x in range(HEADER_SIZE - len(header))]
                Csock.sendall(header)
                Csock.sendall(bytes(padding))

                #发送info
                info_send = info.encode('utf8')
                Csock.sendall(bytes(info_send))

        else:
            print(self.ipaddr + " is not in the routei")
            #不太可能

        pass

    def EXEComm(self):
        """
            先开两个线程，一个用于监听peer的请求，
            另一个用于和tractor交流
            执行命令的函数
            命令如SHOW,GET fileName
        """
        # 输入并执行命令
        while(1):
            cmdLine = str(input(">>> "))
            if cmdLine == 'help':
                print("you can press: ")
                print("  'show' to get all of the peer's message")
                print("  'get [filename]' to download the file")
                print("  'ask [destIp]' to ask the route information")
                print("  'trans [destIp]' to trans info to the [destIp]")
                print("  'quit' to exit the p2p")
            elif cmdLine == 'show':
                self.show()
            elif cmdLine[:3] == 'get':
                self.getFile(cmdLine[4:])
            elif cmdLine[:3] == 'ask':
                self.askRoute(cmdLine[4:])
            elif cmdLine[:4] == 'tran':
                dest = self.askRoute(cmdLine[5:])
                info = str(input(">>> Please input the information you want to trans:\n"))
                info = self.ipaddr + " " + info
                self.transmiss(dest, info)
            elif cmdLine[:4] == 'quit':
                #关闭所有线程
                break


if __name__ == '__main__':
    c = Router()
    c.EXEComm()
