## application_virtual_routing

centralized_routing



### v1.0

#### 文件分类

1. Controller.py：控制器代码
2. Router.py：路由器代码
3. tools.py：一些函数

#### 协议明确

1. 总体介绍：控制器负责处理各个路由器的上线和下线，每个路由器都存储着当前的路由表，路由器要发送数据时，会根据路由表使用链路状态的协议选择最短路径，除非有别的路由器上线或者下线，路由表不会改变

2. 具体实施：

   1. 路由器上线：

      Router -> Controller：WANT ON

      ​

      Controller：随机选择已上线的IP（个数随机）与该新上线ip邻接，并随机设置距离（邻接和距离信息存储在一个邻接表中：map<str,map<str,int>> adjlist）；根据邻接表计算每两个节点间的最短路径，并将结果存储在另一个字典中，map<str,map<str,str>> pathlist，比如ip3=pathlist\[ip1][ip2]表示在ip1到ip2的最短路径中，ip1的下一跳是ip3。这样就生成了每一个路由器的路由表（pathlist[ip1]就是路由器ip1的路由表

      ​	-> all Router：ON msgsize,  msg(该路由器的路由表pathlist[x]��S�N�v0)

      all Router：接收信息并修改本地路由表（添加）

      ​

      each Router：接收信息并更新本地路由表

      ​	-> Controller：ON finish

      ​

      Controller：接收所有的finish信息，接收完成则

      ​	-> 之前想上线的Router：ON end

   2. 路由器下线：

      Router -> Controller：WANT OFF

      ​

      Controller：在邻接表中删除想下线的路由器IP，重新计算任意两个节点之间的最短路径，并更新pathlist

      ​	-> each Router (except 想要下线的Router)：OFF msgsize msg(该路由器的路由表pathlist[x])

      ​

      each Router：接收后，

      ​	-> Controller：OFF finish

      ​

      Controller：接收所有的finish信息，接收完成则

      ​	-> 之前想下线的Router：OFF end

   3. 路由表实现：

      ```python
      map<str, str>  routeList
      routeList[ipdest] = nextIP
      ```

   4. 路由器直接发送数据：

      src Router1：sent  ipdest，判断输入是否合法（由本地实现）

      ​	data_sent = input()

      ​	算出路由路径，得出下一跳

      ​	-> 下一跳：SENT ipsrc ipdest msgsize,  msg(data_sent)

      中间Router：接收信息，由ipdest获取下一跳

      ​	->下一跳：SENT ipsrc ipdest msgsize,  msg(data_sent)

      dest Router2：接收信息，输出

      ​	->src Router1：SENT OK ipsrc ipdest

      中间路由：接收信息

      ​	-> SENT OK ipsrc ipdest

      src Router1：收到回复了

   5. 控制器存储路由器的实现：一个列表存储全部上线的路由器的IP，[ip1, ip2, ip3, ....]

#### 一些函数或语法

1. 列表与字符串的相互转换

   ```python
       str --> list  string.split(' ')
       list --> str  string.join(list)  

       list = ['a', 'b']
       ','.join(list) --> 'a,b'
   ```

2. 多线程的使用

   ```python
   import threading

   while True:

               conn, addr = self.serverSocket.accept()          

               p = threading.Thread(target=self.handle, args=(conn,addr, ))

               p.start()
   ```

3. 建立套接字

   ```python
   #Client:
   self.Tsock = socket.socket()
   self.Tsock.connect((tractorAddr, tractorPort))

   #Server:
   self.serverSocket = socket.socket()

   self.serverSocket.bind(('127.0.0.1', port))

   self.serverSocket.listen(MaxConnect)
   ```

4. 发送接收数据

   ```python
   #从连接读取指定长度的数据
   HEADER_SIZE= 32

   #获取size大小的数据，存储在data里
   def readNbytes(conn, data, size):
       count = 0
       #recv流式读取，可能不能一次性全部读取完
       while count != size:
           buffer = conn.recv(size - count)
           data[count:count + len(buffer)] = buffer
           count += len(buffer)

   #获取头部字符串
   def getHeader(conn, size = HEADER_SIZE):
       data = [0 for x in range(size)]
       readNbytes(conn, data, size)
       header = bytes(data).decode()
       return header.strip()

   #Client:
           header = header.encode('utf8')
           padding = [32 for x in range(HEADER_SIZE - len(header))]
           self.Tsock.sendall(header)
           self.Tsock.sendall(bytes(padding))
           self.Tsock.sendall(send_data)
           
           
   #Server:
   	    header = "SET OK".encode('utf8')
           padding = [32 for x in range(HEADER_SIZE - len(header))]
           conn.send(header)
           conn.send(padding)
           
   ```

   ​

5. 打开文件

   ```python
               with open(newFileName, 'ab') as fw:
                   for i in range(len(ipList)):
                       #读取分片文件 
                       with open(fileName + '_temp' + str(i), 'rb') as fr:
                           for line in fr.readlines():
                               fw.write(line)
   ```

   ​

6. 补充，加油



