from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives import serialization 
from multiprocessing import Queue
import os
import json
import socket
import time
import threading

from HashDigest import HashDigest
from CrewSign import CrewSign, ClntSign
from Config import WrkrConfig
from CT0Discover import Discover
from CT0Fetch import Fetch


# structure received by hosts
class msgPacket:
    packet = None

    def __init__(self, wrkrcon = None, comm = None, sender = None, receiver = None, channel = None, tag = None, messageStruct = None):
        self.packet = {}
        if wrkrcon != None and comm != None and sender != None and receiver != None and channel != None and tag != None and messageStruct != None:
            self.makeAData(sender, receiver)
            self.makeCData(channel, tag, messageStruct)
            dataToSign = self.makeSData()
            self.makeVData(wrkrcon, comm, dataToSign, receiver, sender)                       

    def makeAData(self, sender, receiver): #sender/receiver: [], [<crewID>], [<crewID>,<address>]
        #Sender:
        #1.client--->client comm : []        N.A.
        #2.in crew comm broadcast : [<crewID>,<address>]
        #3.in crew comm response : [<crewID>,<address>]
        #4.leader crew--->client comm : [<crewID>]
        #5.leader crew--->crew comm : [<crewID>]
        #6.client--->crew comm : []          N.A.
        self.packet['sender'] = sender
        #Receiver:
        #1.client--->client comm : []        N.A.
        #2.in crew comm broadcast : [<crewID>]
        #3.in crew comm response : [<crewID>,<address>]
        #4.leader crew--->client comm : []   N.A.
        #5.leader crew--->crew comm : [<crewID>]
        #6.client--->crew comm : [<crewID>]
        self.packet['receiver'] = receiver

    def makeCData(self, channel, tag, messageStruct):
        message = messageStruct
        if isinstance(messageStruct, str) == False:
            message = messageStruct.toString()
        self.packet['message'] = message
        self.packet['tag'] = tag
        self.packet['channel'] = channel

    def makeSData(self):
        sdata = {}
        sdata['message'] = self.packet['message']
        sdata['tag'] = self.packet['tag']
        sdata['channel'] = self.packet['channel']
        return json.dumps(sdata)

    def makeVData(self, wrkrcon, comm, commData, receiver, sender):
        Sign = CrewSign(wrkrcon, comm)
        data = ""
        if len(sender) == 2:  #2. in crew comm broadcast   #3. in crew comm response
            data = Sign.sign(commData, 'resp')
        elif len(sender) == 1:  #4. leader crew client comm   #5. leader crew crew comm
            data = Sign.sign(commData, 'init')
        elif isinstance(sender, str):
            data = Sign.sign(commData, 'resp')
        if not isinstance(data, str):
            data = Sign.toString(data)
        self.packet['signature'] = data

    def makeStruct(self, typeIndicator, stringData):
        #convert string to structure according to type
        if typeIndicator == 'message':
            return stringData
        #CREW SIGN types
        if typeIndicator == 'crewSign':
            return stringData
        if typeIndicator == 'crewSignResp':
            return stringData
        #SELECT CELL types
        if typeIndicator == 'selectCell':
            return stringData
        if typeIndicator == 'selectCellAck':
            return stringData
        #FETCH types
        if typeIndicator == 'fetchCell':
            return stringData
        if typeIndicator == 'fetchCellOK':
            return stringData
        if typeIndicator == 'fetchCrew':
            return stringData
        if typeIndicator == 'fetchCrewOK':
            return stringData
        #CREATE NODE types
        if typeIndicator == 'newcrew': #1
            return stringData
        if typeIndicator == 'newcrewAck': #2
            return stringData
        if typeIndicator == 'createNode': #5, #7-new mem
            return stringData
        if typeIndicator == 'createNodeAck': #6
            return stringData
        if typeIndicator == 'createNewNode': #8-monitors
            return stringData
        if typeIndicator == 'inviteHost': #3
            return stringData
        if typeIndicator == 'inviteHostAck': #4
            return stringData
        #ASSIMILATION types
        if typeIndicator == "leafwardPOA":
            return stringData
        if typeIndicator == "rootwardAD":
            return stringData
        if typeIndicator == "rwNonce":
            return stringData
        return None

    def toString(self):
        return json.dumps(self.packet)

    def parse(self, stringMsg: str):
        self.packet = json.loads(stringMsg)

    def isSession(self):
        # only need to check among "initiating tags"
        return True




class Communication:

    def __init__(self, con):
        self.channelList = ["rwNonce", "rootwardAD", "leafward", "createNode", "selectCell", "fetch", "crewSign", "crewSignResp"] #etc
        self.initiatorTags = ["crewSign", "selectCell", "fetchCell","getCrew","newcrew","createNode"]
        self.readconfig(con)
        self.initCommQueues()  #  { nodeID: {channel: buffer}}
        self.buffersz = 2**25
        self.Soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.Soc.bind((self.IP, int(self.PORT))) 

    def readconfig(self, con):
        #-----read host credentials
        self.private_key = con.fig['pvtkey']
        self.public_key = con.fig['pubkey']
        self.address = con.fig['addr']
        self.IP = con.fig['IP']
        self.PORT = con.fig['port']

    def initCommQueues(self):
        self.commQueues = {}
        self.commQueues[self.address] = {} #create node host
        self.commQueues[self.address]["createNode"] = Queue()
        self.commQueues[self.address]["fetch"] = Queue()

    def addCommQueue(self, wrkr):
        self.commQueues[wrkr.con.nodeID] = {}
        for channel in self.channelList:
            self.commQueues[wrkr.con.nodeID][channel] = Queue()

#SESSION INITIATOR SIDE---------------

    # starts a session -- establishes connections with all wrkrs in nodeID
    def connectTo(self, wrkrcon, nodeID):
        members = wrkrcon.getCrewInfo(nodeID)
        if members == None:
            print("crew not found. Discovering...")
            F = Fetch(wrkrcon, self)
            D = Discover(wrkrcon, F)
            crews = D.discoverFetch(nodeID, 'root')
            members = crews[0]
            #members = wrkrcon.getCrewInfo(nodeID)
            
        if isinstance(wrkrcon, WrkrConfig):
                if self.address in members and nodeID == wrkrcon.nodeID:
                    members.remove(self.address)
        socks = []
        for rec in members:
                netInfo = self.getNWInfo(rec, wrkrcon)
                host = netInfo[0]
                port = netInfo[1]
                addr = (host, port)
                try:
                        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        #conn.bind((self.IP, int(self.PORT)))
                        conn.connect(addr)
                        socks.append(conn)
                        self.thrd(self.addToMessageQueue, (conn, addr))
                except:
                        print("connection refused :", addr)
        return socks
    
    def connectToHost(self, wrkrcon, hostaddr):
        netInfo = self.getNWInfo(hostaddr, wrkrcon)
        host = netInfo[0]
        port = netInfo[1]
        addr = (host, port)
        socks = None
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #conn.bind((self.IP, int(self.PORT)))
            conn.connect(addr)
            socks = conn
            self.thrd(self.addToMessageQueue, (conn, addr))
        except:
            print("connection refused :", addr)
        return socks


##SESSION RESPONDER SIDE----

    #close connection from responder side
    def disconnect(self, cnxns):
        #print(cnxns)
        for conn in cnxns:
            keys = list(self.connThreads.keys())
            for c in keys:
                if c.getsockname() == conn.getsockname() and c.getpeername() == conn.getpeername():
                    self.connThreads[c][1] = 0
                    self.connThreads[c][0].join()
                    del self.connThreads[c]
                    c.close()
                    conn.close()
                    #print('DISCONN~')
                    break
        #print("out disconn")

    def listen(self):
        self.Soc.listen()
        self.connThreads = {} #dictionary conn : thread
        while True:
            conn, addr = self.Soc.accept()
            #print("Connected by",addr)
            self.thrd(self.addToMessageQueue, (conn, addr))

    def thrd(self, target, args=()):
        t = threading.Thread(target=target, args=args)
        conn = args[0]
        self.connThreads[conn] = [t, 1] #ctr for number of nested sessions
        self.connThreads[conn][0].start()

    def addToMessageQueue(self, conn, addr):
        time.sleep(1)
        conn.settimeout(10)
        while True:
            try:
                data = conn.recv(self.buffersz)
                if data:
                    pkt = msgPacket(comm = self)
                    pkt.parse(data.decode())
                    receiver = pkt.packet['receiver']
                    if not isinstance(receiver, str):
                        receiver = receiver[0]
                    channel = pkt.packet['channel']
                    #if pkt.packet['tag'] == 'rwNonce':
                    #    print(data.decode())
                    self.commQueues[receiver][channel].put([pkt,conn])
                    break
            except:
                pass
            time.sleep(1)
            if self.connThreads[conn][1] == 0:
                break
        #print("out of loop")

    def sendMessage(self, wrkrcon, cnxns, sender, receiver, channel, tag, messageStruct):
        msgpkt = msgPacket(wrkrcon, self, sender, receiver, channel, tag, messageStruct)
        self.communicate(msgpkt.toString(), cnxns)

    def getMessage(self, wrkrcon, cnxn, channel, tag = None, source = None): #mode: tag,sender; tag; sender
        #print("getMessage:", wrkrcon.nodeID, channel, tag)
        response = None
        while True:
                time.sleep(1)
            #tempq = []
            #for i in range(self.commQueues[wrkrcon.nodeID][channel].qsize()):
                receiver = self.address
                if isinstance(wrkrcon, WrkrConfig):
                    receiver = wrkrcon.nodeID
                msgConn = self.commQueues[receiver][channel].get() #[msgPacket, conn]
                msg = msgConn[0]
                sender = msg.packet['sender']
                stag = msg.packet['tag']
                message = msg.packet['message']
                Sign = CrewSign(wrkrcon, self)
                vdata = msg.makeSData()
                conn = msgConn[1]
                
                if Sign.verify(sender, vdata, msg.packet['signature']):       #sending array sender to verify!!
                    #print("check 1 pass")   print(source, sender, tag, stag)
                    if (source == None or source == sender) and (tag == None or tag == "" or tag == stag):
                        #print("check 2 pass")
                        if cnxn == None:
                            #print("all checks passed")
                            message = msg.makeStruct(stag, message)
                            response = [sender,stag,message,conn]
                            return response
                        elif cnxn.getsockname() == conn.getsockname() and conn.getpeername() == cnxn.getpeername():
                            message = msg.makeStruct(stag, message)
                            response = [sender,stag,message,conn]
                            return response
                    self.commQueues[receiver][channel].put(msgConn)
                        #tempq.append(msgConn)
            #for MC in tempq:
                #self.commQueues[wrkrcon.nodeID][channel].put(MC)
            #if response != None:
                #return response

    def getInCrewResponse(self, wrkrcon, cnxns, channel, tag, mode=None):        #get message set with tag
        responseSet = []
        #print("tag" , tag)
        #print("channel" , channel)
        crew = wrkrcon.members
        #while len(responseSet) != len(crew)-1 :
        if cnxns != None:
            for conn in cnxns:
                c = self.getMessage(wrkrcon, conn, channel, tag)
                if c != None:
                    if c[0][1] in crew:
                        responseSet.append(c)
        else:
            setSize = 0
            if mode == 'init':
                setSize = len(crew)-1
            elif mode == 'resp':
                setSize = len(crew)-2
            while len(responseSet) != setSize:
                #print("getting message")
                c = self.getMessage(wrkrcon, cnxn=None, channel=channel, tag=tag)
                if c != None:
                    if c[0][1] in crew:
                        responseSet.append(c)
        return responseSet

    def getNWInfo(self, address, wrkrcon):
        path = ""
        if isinstance(wrkrcon, WrkrConfig):
            path = wrkrcon.hostcon.fig['addressbook']
        else:
            path = wrkrcon.fig['addressbook']
        f = open(path, "r")
        text = f.read()
        f.close()
        dir = json.loads(text)
        IP = dir[address][0]
        port = dir[address][1]
        return [IP, port]

    def communicate(self, textMsg, cnxns): #cnxns -- made for initiators, pass as args for responders
        for conn in cnxns:
            #print(textMsg)
            conn.sendall(textMsg.encode('utf-8'))





class ClntCommunication:

    def __init__(self, con):
        self.con = con
        self.channelList = ["fetch"] #etc
        self.buffersz = 2**35 # XXX: Avoid a fixed buffersz. Read short fixed length packet announcing message size.

    # establish connections with con.fig['numCrewConnects'] crew members 
    def connectTo(self, nodeID):
        members = self.con.getCrewInfo(nodeID)
        socks = []
        maxcon = int(self.con.fig['numCrewConnects'])
        for rec in members:
            if len(socks) == maxcon:
                break
            netInfo = self.getNWInfo(rec)
            host = netInfo[0]
            port = netInfo[1]
            try:
                soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                soc.connect((host, port))
                socks.append(soc)
            except:
                print("connection refused :",host,port)
        return socks

    def getNWInfo(self, address):
        path = self.con.fig['addressbook']
        f = open(path, "r")
        text = f.read()
        f.close()
        dir = json.loads(text)
        IP = dir[address][0]
        port = dir[address][1]
        return [IP, port]

    # send a message that is similar to one from Connections.sendMessage
    def sendMessage(self, cnxns, channel, tag, messageStruct, dest = None):
        msg = clntMsgPacket([], dest, channel, tag, messageStruct)                
        text = msg.toString()
        for soc in cnxns:
            soc.sendall(text.encode('utf-8'))

    def getMessage(self, cnxns, channel = None, tag = None, source = None): #mode: tag,sender; tag; sender
        # read from all sockets (return if any works)
        msgdata = ""
        while True:
            flag = False
            for conn in cnxns:
                #print("getMessage:", tag, "reading from:", str(conn))
                data = conn.recv(self.buffersz)
                if data is not None:
                    msgdata = data
                    flag = True
                    break
            if flag == True:
                break
        msg = clntMsgPacket()
        msg.parse(data.decode())
        sender = msg.packet['sender']
        VData = msg.makeSData()
        smessage = msg.packet['message'] 
        schannel = msg.packet['channel']
        stag = msg.packet['tag']
        message = msg.makeStruct(stag, smessage)
        #return [sender, stag, message]
        #print(channel, source, tag)
        #print(schannel, sender, stag)
        if channel is not None and channel != schannel:
            return None
        if source is not None and source != sender:
            return None
        if tag is not None and tag != "" and tag != stag:
            return None
        # verify that the message is signed by the entire crew
        #print("checks passed")
        Sign = ClntSign(self.con)
        if not Sign.verify(sender, VData, msg.packet['signature']): #sending array sender to verify!!
            return None
        return [sender,stag,message]

    def disconnect(self, cnxns):
        for soc in cnxns:
            soc.close()



class clntMsgPacket:
    packet = None

    def __init__(self, sender = None, receiver = None, channel = None, tag = None, messageStruct = None):
        self.packet = {}
        if channel != None and tag != None and messageStruct != None:
            self.makeAData(sender, receiver)
            self.makeCData(channel, tag, messageStruct)
            self.makeVData()                       

    def makeStruct(self, typeIndicator, stringData):
        #convert string to structure according to type
        if typeIndicator == 'message':
            return stringData
        #FETCH types
        if typeIndicator == 'fetchCell':
            return stringData
        if typeIndicator == 'fetchCellOK':
            return stringData
        if typeIndicator == 'fetchCrew':
            return stringData
        if typeIndicator == 'fetchCrewOK':
            return stringData
        return None
    
    def makeAData(self, sender, receiver): #sender/receiver: [], [<crewID>]
        #Sender:
        #2.client--->crew comm : []
        #3.leader crew---->client comm : [<crewID>]        
        self.packet['sender'] = sender
        #Receiver:
        #2.client--->crew comm : [<crewID>]
        #3.leader crew--->client comm : [] 
        self.packet['receiver'] = receiver

    def makeCData(self, channel, tag, messageStruct):
        message = messageStruct
        if isinstance(messageStruct, str) == False:
            message = messageStruct.toString()
        self.packet['message'] = message
        self.packet['tag'] = tag
        self.packet['channel'] = channel

    def makeVData(self):
        self.packet['signature'] = '{}'

    def makeSData(self):
        sdata = {}
        sdata['message'] = self.packet['message']
        sdata['tag'] = self.packet['tag']
        sdata['channel'] = self.packet['channel']
        return json.dumps(sdata)

    def toString(self):
        return json.dumps(self.packet)

    def parse(self, stringMsg: str):
        #print("message received ", stringMsg)
        self.packet = json.loads(stringMsg)



