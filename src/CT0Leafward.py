import random
import time
from CT0Store import POA
from Procedures import Procedures



class Leafward:
        POA = None
        
        def __init__(self, wrkr):
                self.wrkr = wrkr
                self.wrkrcon = wrkr.con
                self.nodeID = wrkr.con.nodeID
                self.C = wrkr.host.comm
                self.POA = POA(None, None, wrkr.con)        #POA(merklepath, sign, wrkrcon)                
                self.startLW = False

        def sendMessage(self, cnxns, rcvr, tag, msg):
                sender = [self.nodeID]
                self.C.sendMessage(self.wrkrcon, cnxns, sender, rcvr, "leafward", tag, msg)

        def getMessage(self, tag, sender):
                return self.C.getMessage(self.wrkrcon, None, "leafward", tag, sender)

        def listener(self):                #THREAD: get POA from parent, store and update
                sender = [self.nodeID[:-1]]
                if len(self.nodeID) == 1:
                        sender = ["root"]
                #cnxns = self.C.connectTo(self.wrkrcon, sender)
                while True:
                        c = self.getMessage("leafwardPOA",sender)
                        if c != None:                #print(c)
                                conn = c[3]
                                self.C.disconnect([conn])
                                msg = c[2]
                                #print("got a POA", self.nodeID)
                                #print("MSG : ", msg)
                                #print("existingPOA : ", self.POA.toString())
                                lPOA = POA(None, None, self.wrkrcon)
                                lPOA.parse(msg)
                                #lPOA.printPOApath()
                                #print(msg)
                                #print(lPOA.merklePathStr() != self.POA.merklePathStr())
                                if lPOA.merklePathStr() != self.POA.merklePathStr():
                                    self.POA = lPOA
                                    self.startLW = True


        def scheduler(self):        #THREAD: trigger leafward procedure -- done in listener
            while True:
                time.sleep(10)#100*len(self.nodeID))
                if self.startLW:
                    #print("starting LW", self.nodeID)
                    Procedures.leafward(self.wrkr)
                    self.startLW = False

        def receive(self):
                return ['root', None, self.POA]
                
        def pickLeaves(self, rootID):
                return [self.nodeID+"0", self.nodeID+"1"]
                        
        def send(self, POASet):
                #POASet[leaf] = [mPath, sign]
                for leaf in POASet:
                        poa = POA(POASet[leaf].merklePath, POASet[leaf].sign, self.wrkrcon)
                        stringPOA = poa.toString()
                        receiver = [leaf]
                        cnxns = self.C.connectTo(self.wrkrcon, receiver[0])
                        if cnxns == None:
                                return None
                        self.sendMessage(cnxns, receiver, "leafwardPOA", stringPOA)
                        self.C.disconnect(cnxns)



