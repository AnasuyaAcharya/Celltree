import time
import threading
import json

from CT0Store import AssimData, UUList
from Procedures import Procedures
from CrewSign import CrewSign


class Rootward:
        ADold = None
        ADnew = None
        Nonce = None
        
        def __init__(self, wrkr):
                self.wrkr = wrkr
                self.wrkrcon = wrkr.con
                self.nodeID = wrkr.con.nodeID
                self.C = wrkr.host.comm
                self.S = CrewSign(self.wrkrcon, self.C)
                self.ADold = AssimData(wrkr.con)
                self.ADnew = AssimData(wrkr.con)
                self.monitorLevels = int(wrkr.con.fig['monitoringDepth'])
                self.rootwardEpoch = int(wrkr.con.fig['rootwardEpoch'])
                phaseshift = int(wrkr.con.fig['rootwardPhaseShift'])
                nodeDepth = len(self.nodeID)
                if self.nodeID == 'root':
                    nodeDepth = 0
                self.rootwardPhase = (4 - (nodeDepth % 4)) * phaseshift

        def sendMessage(self, cnxns, rcvr, tag, msg):
                sender = []
                if tag == "rootwardAD":
                    sender = [self.nodeID]
                elif tag == "rwNonce":
                    sender = [self.nodeID, self.wrkrcon.hostcon.fig['addr']]
                    #print("sending NONCE: ", cnxns, sender, rcvr, tag, msg)
                self.C.sendMessage(self.wrkrcon, cnxns, sender, rcvr, tag,tag,msg)#"rootward", tag, msg)

        def getMessage(self, tag):
                return self.C.getMessage(self.wrkrcon, None, tag, tag)#"rootward", tag)
                
        def listener(self):                #THREAD: get assimData from child, store and update
                ADt = threading.Thread(target=self.ADlistener, args=())
                ADt.start()
                Nt = threading.Thread(target=self.Noncelistener, args=())
                Nt.start()
            
        def ADlistener(self):
                while True:
                        c = self.getMessage("rootwardAD")
                        if c != None:                #print(c)
                                msg = c[2]
                                sender = c[0]
                                self.ADnew.append(msg)
                                #print("Assim Signal: ", msg)
                                conn = c[3]
                                self.C.disconnect([conn])

        def Noncelistener(self):
                while True:
                        c = self.getMessage("rwNonce")
                        if c != None:
                                msg = c[2]
                                sender = c[0]
                                if sender[1] in self.wrkrcon.members:
                                    self.Nonce = msg
                                    #print("nonce received", msg)
                                conn = c[3]
                                self.C.disconnect([conn])

        def getNonce(self):
            if self.Nonce == None:
                self.Nonce = self.wrkrcon.hasher.generateNonce()
                cnxns = self.C.connectTo(self.wrkrcon, self.nodeID)
                if cnxns != None and cnxns != []:
                    self.sendMessage(cnxns, [self.nodeID], "rwNonce", self.Nonce)
                    #print("nonce sent", cnxns)
                    self.C.disconnect(cnxns)
                    #print("nonce sent", self.Nonce)
            Nonce = self.Nonce
            self.Nonce = None
            return Nonce

        def scheduler(self):        #THREAD: trigger rootward procedure
                #TODO: the phase shift should look at current time
                time.sleep(self.rootwardPhase)
                while True:
                        print("******ROOTWARD********\n\n\n\n\nROOTWARD",self.nodeID)
                        Procedures.rootward(self.wrkr)
                        time.sleep(self.rootwardEpoch)

        def receive(self, nodeID):
                if nodeID in self.ADnew.AssimSignalDict.keys():
                        return self.ADnew.AssimSignalDict[nodeID]
                else:
                        return None
                
        def monitored(self):
                nodeIDList = []
                for i in range(self.monitorLevels):
                        #generate all binary strings of length i+1
                        for x in range(2**(i+1)):
                                suffix = str(bin(x))[2:]
                                if len(suffix) != i+1:
                                        for y in range(i+1-len(suffix)):
                                                suffix = '0'+suffix
                                if self.nodeID != 'root':
                                        nodeIDList.append(self.nodeID+suffix)
                                else:
                                        nodeIDList.append(suffix)
                return nodeIDList
                
        def send(self, uulist, mNode):
                #sends assimData to parent
                self.ADold.update(self.ADnew.toString())
                stringNewData = {}
                textnode = ""
                textUUlist = ""
                if mNode != None:
                        textnode = mNode.toString() 
                if uulist != None:   
                        uul = UUList()
                        for n in uulist:
                                uul.add(n)
                        textUUlist = uul.toString()
                        message = json.dumps([textnode, textUUlist])
                        sign = self.S.sign(message, "init")
                        textSign = self.S.toString(sign)
                        stringNewData[self.nodeID] = json.dumps([textnode, textUUlist, textSign])
                        stringNewData = json.dumps(stringNewData)
                        self.ADnew.append(stringNewData)
                        stringAD = self.ADnew.toString()
                        receiver = [self.nodeID[:-1]]
                        if len(self.nodeID) == 1:
                                receiver = ["root"]
                        if self.nodeID == "root":
                                return #receiver = "crew"+self.nodeID[:-1]
                        cnxns = self.C.connectTo(self.wrkrcon, receiver[0])
                        if cnxns == None:
                                return None
                        self.sendMessage(cnxns, receiver, "rootwardAD", stringAD)
                        self.C.disconnect(cnxns)

