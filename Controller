import socket
import hashlib
import multiprocessing
import time
from tools import *

import os


'''
添加路由表(成员变量)
修改recv函数里的handle, peer上线时, 分配peer与其相连, 修改Tractor的路由表(随机确定链路代价)
添加peer路由请求回应方法
修改EXEComm函数，添加路由请求回应
'''

class Controller():

    def __init__(self, port=5555, MaxConnect=10):
        """

            初始化函数，会根据参数建立socket连接。并设置侦听数量，但是要获得连接，使用recv函数

            port=5555:指定端口用于连接

            MaxConnect=5:指定最大连接数 

            resourceMap: dict, (file(str): [(str(ip)...])

            routing_table: dict, (str(ip_src): [str(ip_dest), int(dis)])
        """

        self.port = port

        self.serverSocket = socket.socket()

        self.serverSocket.bind(('127.0.0.1', port))

        self.serverSocket.listen(MaxConnect)

        # 空字典。resourceName --> ip set

        # 保存资源与IP之间的关系

        mgr = multiprocessing.Manager()
        self.resourceMap = mgr.dict()

        self.routing_table = dict()

        # 保存存活ip

        self.live = set()

    def recv(self):
        """

            接受函数。。。

            无参数

            接受连接，并建立相应的线程处理连接。

            线程函数为handle

        """

        while True:

            conn, addr = self.serverSocket.accept()          

            p = multiprocessing.Process(target=self.handle, args=(conn, addr, self.resourceMap, ))

            p.start()

    def handle(self, conn, addr, resourceMap):
        """

            处理函数，处理客户端的资源请求与响应

            conn:连接套接字

            addr:客户端地址

            一开始要存储客户端本地的文件名，修改resourceMap
            Peer: HAVE MESSIZE MSG
            Tractor: HAVE OK

            然后修改路由表
            Peer: ROUT MESSIZE MSG([[srcip, destip, dis]...])
            Tractor: SET OK

        """

        # 期待从peer获得资源信息。

        # 以下是过程描述

        # Peer: HAVE MESSIZE MSG

        # Tractor: HAVE OK

        # 将客户端的地址加入存活列表，

        self.live.add(addr)

        # 获取头部信息

        header = getHeader(conn)

        print(header)

        if header[0:4] == 'HAVE':

            # OK

            msgSize = int(header[5:])

            data = [0 for x in range(msgSize)]

            readNbytes(conn, data, msgSize)

            # 获取得到的资源信息(文件名,文件名)

            msg = bytes(data).decode()

            fileList = msg.split(",")

            # 保存资源与ip的映射关系
            
            print(resourceMap)

            for fileName in fileList:

                if fileName not in resourceMap:
                     resourceMap[fileName] = addr[0]
                else:
                    resourceMap[fileName] += ' ' + addr[0]
                
            # 发送头部信息
            print(resourceMap)

            header = 'HAVE OK'.encode('utf8')

            padding = [32 for x in range(HEADER_SIZE - len(header))]
            
            conn.sendall(header)

            conn.sendall(bytes(padding))

        else:

            # 应该不可能吧

            pass

        # 至此，客户端只会向跟踪服务器请求资源信息。

        # 阻塞于此。

        while True:

            header = getHeader(conn)

            self.EXEComm(header,conn)

    def replySHOW(self, conn):
        """

            处理客户端SHOW的请求(下面的并非参数)

            client: SHOW

            Tractor:SHOW OK fileName, fileName...

        """

        # 返回一个资源列表(文件名,文件名)

        send_data = ','.join(list(self.resourceMap.keys())).encode('utf8')
        header = ('SHOW OK ' + str(len(send_data))).encode('utf8')
        padding = [32 for x in range(HEADER_SIZE - len(header))]
        print(header)
        conn.sendall(header)
        conn.sendall(bytes(padding))
        conn.sendall(send_data)

    def replyGET(self, filename, conn):
        """

            接收客户需要的文件名

            将拥有该文件的peer的ip传给客户

        """

        # 获取拥有文件的对等方的ip
        filename = filename.strip()
        iplist = self.resourceMap[filename].split(' ')
        
        print("junyi1")
        print(iplist)
        ipset = ','.join(iplist).encode('utf8')
        print("junyi2")
        print(ipset)
        header = ('GET OK ' + str(len(ipset)) + ' ').encode('utf8')
        print(header)

        padding = [32 for x in range(HEADER_SIZE - len(header))]

        conn.sendall(header)

        conn.sendall(bytes(padding))

        conn.sendall(ipset)

    def replyROUTE(self, conn, addr, destip):
        """
            conn: 提出请求的peer
            destip: 请求访问的ip地址
            使用算法求出在路由表中addr[0] -> destip 的最短路径

            Tractor: ROUTE OK MESSIZE
                     addr[0], ... , destip

        """
        pass 

    def EXEComm(self, header, conn):

        if header[:4] == 'SHOW':

            self.replySHOW(conn)

        elif header[:3] == 'GET':

            filename = header[4:]

            self.replyGET(filename, conn)


if __name__ == '__main__':

    t = Controller()

    t.recv()

    pass
