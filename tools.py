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


