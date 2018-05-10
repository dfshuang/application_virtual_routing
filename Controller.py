import socket
import hashlib
import threading
import time
from tools import *

import os








'''错误重复的信息
    每个路由器会保持一个和controller之间的连接。定时发送在线信息并更新路由表。
    路由器和路由器之间的连接是固定的，但是数据包转发的连接时由路由表决定的。
    简易IP报文格式:(sourceIp,destinationIp,msgsize)msg
    注意Router和Controller之间的信息交换应该是通过广播或者底层协议。（这里使用链路层协议，即直接通信）

    Router与Controller之间（链路层协议）：
    Router:(GET Table itemsize)items
    Controller:(GET OK tabsize)table

    Router会通过路由表选择合适的连接转发数据报。

'''






'''
添加路由表(成员变量)
修改recv函数里的handle, peer上线时, 分配peer与其相连, 修改Tractor的路由表(随机确定链路代价)
添加peer路由请求回应方法
修改EXEComm函数，添加路由请求回应
'''

class Controller():

    def __init__(self, port=5555, MaxConnect=100):
        """

            初始化函数，会根据参数建立socket连接。并设置侦听数量，但是要获得连接，使用recv函数

            port=5555:指定端口用于连接

            MaxConnect=100:指定最大连接数 

            resourceMap: dict, (file(str): [(str(ip)...])

            routing_table: dict, (str(ip_src): [str(ip_dest), int(dis)])
        """

        self.port = port

        self.serverSocket = socket.socket()

        self.serverSocket.bind(('127.0.0.1', port))

        self.serverSocket.listen(MaxConnect)


        #二阶字典。
        self.routing_table = {}
        while True:

            conn, addr = self.serverSocket.accept()          

            p = threading.Thread(target=self.handle, args=(conn,addr, ))

            p.start()


    def handle(self, conn, addr):
        """

            处理函数，处理客户端的资源请求与响应

            conn:连接套接字

            addr:客户端地址

            然后修改路由表
            Peer: (ROUTE MESSIZE) MSG([[srcip, desti, pdis]...])
            Tractor: SET OK

        """
        self.routing_table[addr] = {}
        #32位头部信息。链路层协议。
        header = getHeader(conn)
        int megSize = int(header.split(' ')[1])
        msg = readNbytes(megSize).decode().strip().split(',')
        #保存计算路由的距离信息。
        for i in range(msg.size/3):
            self.routing_table[msg[3*i]][msg[3*i + 1]] = msg[3*i + 2]
        

        #回复
        header = "SET OK".encode('utf8')
        padding = [32 for x in range(HEADER_SIZE - len(header))]
        conn.send(header)
        conn.send(padding)



    def replyROUTE(self, conn, addr, destip):
        """
            conn: 提出请求的peer
            destip: 请求访问的ip地址
            使用算法求出在路由表中addr[0] -> destip 的最短路径

            Tractor: ROUTE OK MESSIZE
                     addr[0], ... , destip

        """
        

        pass 

 


if __name__ == '__main__':

    t = Controller()

    t.recv()

    pass
