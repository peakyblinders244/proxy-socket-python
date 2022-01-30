import sys, threading, socket, queue

MAX_DATA_REVC = 2048
HOST = "127.0.0.1"
PORT = 8888
thread_count = 2

queueLock = threading.Lock()
workQueue = queue.Queue(10001)

class packet:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr

class webInfor:
    def __init__(self, method, host, url, port, data):
        self.method = method
        self.host = host
        self.url = url
        self.port = port
        self.data = data

class myThread (threading.Thread):# threading inheritance
    def run(self):
        while True:
            try:
                queueLock.acquire()
                if not workQueue.empty():
                    tmp = workQueue.get()
                    Process(tmp.conn, tmp.addr)
                    queueLock.release()
                else:
                    queueLock.release()
            except:
                print("ERROR!")

def getWebInfor(strData):
    str = strData.split()
    method = str[0]
    url = str[1]
    tmp = str[4]

    if tmp.find(':') == 1:
        tmp = tmp.split(':')
        host = tmp[0]
        port = tmp[1]
    else:
        host = tmp
        port = "80"

    if method == "POST":
        strData.split('\r\n\r\n')
        data = strData[1]
    else:
        data = ''

    web = webInfor(method,host,url,port,data)

    return web

def loadBlackList():
    try:
        file = open("blacklist.conf", 'r')
        dataFile = file.read()
        dataFile = dataFile.split()

        return dataFile
    except:
        print("ERROR Black List")
Black_list=loadBlackList() # Create blacklist

def readResponse(webServer):
    data = b''

    webServer.settimeout(2)
    try:
        while True:
            part = webServer.recv(MAX_DATA_REVC)
            data += part
            if len(part) == 0:
                break
    except socket.timeout:
        print("Error: [Time out]!")
    return data

def requestSendToWebServer(web):# check web's method and return request send to web server
    request = ""

    if web.method == "GET":  # check GET method
        if web.port == "80":
            request = "GET " + web.url + " HTTP/1.1\r\n" + "Accept: */*\r\n" + "Host: " + web.host + "\r\n" + "Connection: Close\r\n\r\n"
        else:
            request = "GET " + web.url + " HTTP/1.1\r\n" + "Accept: */*\r\n" + "Host: " + web.host + ":" + web.port + "\r\n" + "Connection: Close\r\n\r\n"
    if web.method == "POST":  # check POST method
        if web.port == "80":
            request = "POST " + web.url + " HTTP/1.1\r\n" + "Accept: */*\r\n" + "Host: " + web.host + "\r\n" + "Content-Type: application/x-www-form-urlencoded\r\n" + "Content-Length: " + web.data.length() + "\r\n\r\n" + web.data
        else:
            request = "POST " + web.url + " HTTP/1.1\r\n" + "Accept: */*\r\n" + "Host: " + web.host + ":" + web.port + "\r\n" + "Content-Type: application/x-www-form-urlencoded\r\n" + "Content-Length: " + web.data.length() + "\r\n\r\n" + web.data

    return request

def Process(conn, client_addr):
    request = conn.recv(MAX_DATA_REVC)
    strData = request.decode("utf8")
    if strData.find("HTTP") == -1 or len(strData) == 0:
        print("#Close connection")
        return
    web = getWebInfor(strData)

    if isForbidden(web.host): # Check black list
        response_403 = "HTTP/1.1 403 Forbidden\r\n\r\n<HTML>\r\n<BODY>\r\n<H1>403 Forbidden</H1>\r\n<H2>You don't have permission to access this server</H2>\r\n</BODY></HTML>\r\n"
        conn.send(response_403.encode())
    else:
        request = requestSendToWebServer(web)
        try:
            webServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            webServer.connect((web.host, int(web.port)))
            webServer.send(request.encode())
            data = readResponse(webServer)
            webServer.close()
            conn.send(data)
            print(web.host)
            print("Connect to web server")
        except:
            print(web.host)
            print("Can't connect to web server")

def isForbidden(host):
    for i in Black_list:
        if host == i:
            return True
    return False

def main():
    threads = []
    for i in (1, thread_count):
        thread = myThread()
        thread.start()
        threads.append(thread)
    try:
        print("Open socket")
        proxyServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxyServer.bind((HOST, PORT))
        proxyServer.listen(10)
    except:
        if proxyServer:
            proxyServer.close()
            print("Could not open socket:")
            sys.exit(1)

    while True:
        try:
            proxyServer.settimeout(0.2)
            conn, addr = proxyServer.accept()
            queueLock.acquire()
            soc = packet(conn,addr)
            workQueue.put(soc)
            queueLock.release()
            print("Accept")
        except:
            print("ERROR")
#main fucntion
if __name__== "__main__":
    main()