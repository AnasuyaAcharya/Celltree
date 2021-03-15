from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives import serialization 
import os
import json
import threading

from Config import Config, CrewInfo
from Cell import Cell, Nucleus
from HashDigest import HashDigest

class CreateNode:
        
        # Takes wrkr itself, to get hold of host, to add to wrkrSet
        def __init__(self, wrkr, comm):
                self.wrkr = wrkr
                self.wrkrcon = wrkr.con
                self.members = self.wrkrcon.members
                self.nodeID = self.wrkrcon.nodeID
                self.address = self.wrkrcon.hostcon.fig['addr']
                self.monitorLevels = int(wrkr.con.fig['monitoringDepth'])
                self.C = comm
                self.H = self.wrkrcon.hasher

        def sendMessage(self, cnxns, rcvr, tag, msg):
            if tag == "newcrew" or tag == "newcrewAck" or tag == "createNodeAck" or (tag == "createNode" and rcvr == [self.nodeID]):
                sender = [self.nodeID, self.address]
            elif tag == "inviteHost" or tag == "createNode" or tag == "createNewNode":
                sender = [self.nodeID]
            self.C.sendMessage(self.wrkrcon, cnxns, sender, rcvr, "createNode", tag, msg)

        def getMessage(self, tag): #all except "inviteHost"
                return self.C.getMessage(self.wrkrcon, None, "createNode", tag)
        
        
        def newNode(self, child, path, mode):        #mode = 'init'/'resp'
                isChild = False
                if not self.wrkrcon.isRoot():
                        if child == self.nodeID+'0' or child == self.nodeID+'1':
                                isChild = True
                else:
                        if child == '0' or child == '1':
                                isChild = True
                if isChild:    #new node id is child
                        if mode == 'init':
                                childCrewMembers = CrewInfo.read(path)
                                #inform new crew of membership + other members
                                stringCrewInfo = CrewInfo.toString(childCrewMembers, child)
                                #protocol to get new crew members
                                flag = self.selectCrew(stringCrewInfo, 'init')
                                if flag:
                                        #update other crew info
                                        p = self.wrkrcon.hostcon.fig['crewsdir']+child
                                        childCrewStr = json.loads(stringCrewInfo)[1]
                                        f = open(p, "w+")
                                        f.write(childCrewStr)
                                        f.close()
                                        #inform other crew members of new node+members
                                        print("informing other crew members")
                                        cnxns = self.C.connectTo(self.wrkrcon, self.nodeID)
                                        if cnxns == None:
                                            return None
                                        self.sendMessage(cnxns, [self.nodeID], 'createNode', stringCrewInfo)
                                        #collect responses?
                                        response = []
                                        response.append(flag)
                                        print("getting acknowledgements...")
                                        responseSet = self.C.getInCrewResponse(self.wrkrcon, cnxns, "createNode", "createNodeAck")  #print(responseSet)
                                        self.C.disconnect(cnxns)
                                        for resp in responseSet:
                                                if resp[2] == "True":
                                                        response.append(True)
                                                else:
                                                        response.append(False)
                                        for r in response:
                                                if r == False:
                                                        return False
                                        #tell new crew members to start
                                        print("telling child crew to start")
                                        for mem in childCrewMembers:
                                            #crew --> client message : crewsign gets approval from members
                                            conn = self.C.connectToHost(self.wrkrcon, mem)
                                            if conn != None:
                                                self.sendMessage([conn], mem, 'createNode', stringCrewInfo)
                                                print("msg sent", mem)
                                                self.C.disconnect([conn])
                                        #send to parent for cascading to monitors
                                        print("sending to parent--cascade to monitors")
                                        if self.nodeID != "root":
                                            parentID = ""
                                            if len(self.nodeID) == 1:
                                                parentID = "root"
                                            else:
                                                parentID = self.nodeID[:-1]
                                            cnxns = self.C.connectTo(self.wrkrcon, parentID)
                                            if cnxns == None:
                                                return None
                                            self.sendMessage(cnxns, [parentID], "createNewNode", stringCrewInfo)
                                            self.C.disconnect(cnxns)
                                        return True
                                else:
                                        return False
                        elif mode == 'resp':
                                print("in-crew createNode response...")
                                stringCrewInfo = path
                                #select crew
                                flag = self.selectCrew(stringCrewInfo, 'resp')
                                if not flag:
                                    return False
                                #wait for leaders permission:
                                c = self.getMessage("createNode")
                                if c != None:
                                    sender = c[0]
                                    crewInfoStr = c[2]
                                    conn = c[3]
                                    if sender[1] in self.members and crewInfoStr == stringCrewInfo:  #if sender in crew
                                        #update other crew info
                                        childCrewStr = json.loads(stringCrewInfo)[1]
                                        p = self.wrkrcon.hostcon.fig['crewsdir']+child
                                        f = open(p, "w+")
                                        f.write(childCrewStr)#childCrewStr)
                                        f.close()
                                        self.sendMessage([conn], sender,'createNodeAck',str(True))
                                    else:
                                        self.sendMessage([conn], sender,'createNodeAck',str(False))
                                    self.C.disconnect([conn])
                                return True
                else:
                        return False

        def selectCrew(self, strCrewInfo, mode):
                print('in Select Crew')
                if mode == 'init':
                        #share with other crew members -- in crew com
                        cnxns = self.C.connectTo(self.wrkrcon, self.nodeID)
                        newcrewOK = True
                        if cnxns != []:
                            self.sendMessage(cnxns, [self.nodeID], 'newcrew', strCrewInfo)
                            print("msg sent")
                            #concensus
                            responseSet = self.C.getInCrewResponse(self.wrkrcon, cnxns=None, channel='createNode', tag='newcrewAck', mode=mode)
                            print("got responses")
                            self.C.disconnect(cnxns)
                            for resp in responseSet:
                                response = json.loads(resp[2])
                                if response[0] == strCrewInfo and response[1] == False:
                                    newcrewOK = False
                                self.C.disconnect([resp[3]])
                        #invite hosts
                        if newcrewOK:
                            #convert strCrewInfo to struct
                            strCrew = json.loads(strCrewInfo)
                            crewMem = CrewInfo.parse(strCrew[1])
                            #for member in dict, send strCrewInfo
                            response = []
                            for mem in crewMem:
                                #crew --> client message : crewsign gets approval from members
                                conn = self.C.connectToHost(self.wrkrcon, mem)
                                if conn != None:
                                    self.sendMessage([conn], mem, 'inviteHost', strCrewInfo)
                                    print("msg sent", mem)
                                    #receive acknowledgement
                                    c = self.getMessage('inviteHostAck')
                                    if c != None:                #print(c)
                                        if c[0] == mem:
                                            msg = c[2]
                                            resp = json.loads(msg)[1]
                                            CS = json.loads(msg)[0]
                                            if CS == strCrewInfo:
                                                response.append(resp)
                                    self.C.disconnect([conn])
                            #return True if all members give positive response
                            print("responses : ",response)
                            for flag in response:
                                if flag == False:
                                    return False
                            return True
                        return False

                elif mode == 'resp':
                        response = json.dumps([strCrewInfo, True])
                        print("in select crew response")
                        cnxns = self.C.connectTo(self.wrkrcon, self.nodeID)
                        newcrewOK = True
                        if cnxns != []:
                            self.sendMessage(cnxns, [self.nodeID], 'newcrewAck', response)
                            print("sent acknowledgement..")
                            responseSet = self.C.getInCrewResponse(self.wrkrcon, cnxns=None, channel='createNode', tag='newcrewAck', mode=mode)
                            print("got responses.")
                            self.C.disconnect(cnxns)
                            #print("disconnected")
                            for resp in responseSet:
                                response = json.loads(resp[2])
                                if response[0] == strCrewInfo and response[1] == False:
                                    newcrewOK = False
                                self.C.disconnect([resp[3]])
                            #print("out")
                        return newcrewOK


        def listener(self):
                NNt = threading.Thread(target=self.newNodelistener, args=())
                NNt.start()
                CNt = threading.Thread(target=self.createNodelistener, args=())
                CNt.start()
        
        def createNodelistener(self): #for parents of new node
                while True:
                        c = self.getMessage("newcrew")
                        if c != None:                #print(c)
                                print("got create node request")
                                sender = c[0]
                                crewStr = c[2]
                                conn = c[3]
                                if sender[1] in self.members:  #if sender in crew
                                        child = json.loads(crewStr)[0]
                                        flag = self.newNode(child, crewStr, 'resp')
                                        print("create node resp mode : ",flag)
                                self.C.disconnect([conn])

        def newNodelistener(self): #for monitors of new node
                while True:
                    c = self.getMessage("createNewNode")
                    if c != None:
                        print("got new node request")
                        sender = c[0]
                        crewStr = c[2]
                        conn = c[3]
                        self.C.disconnect([conn])
                        if sender[0] in self.monitored():
                            #store crew
                            childCrewStr = json.loads(crewStr)[1]
                            child = json.loads(crewStr)[0]
                            if child in self.monitored():
                                p = self.wrkrcon.hostcon.fig['crewsdir']+child
                                f = open(p, "w+")
                                f.write(childCrewStr)#childCrewStr)
                                f.close()
                                if (self.nodeID != "root" and len(child)-len(self.nodeID) < self.monitorLevels):
                                    #send to parent
                                    parentID = ""
                                    if len(self.nodeID) == 1:
                                        parentID = "root"
                                    else:
                                        parentID = self.nodeID[:-1]
                                    cnxns = self.C.connectTo(self.wrkrcon, parentID)
                                    if cnxns == None:
                                        return None
                                    self.sendMessage(cnxns, [parentID], "createNewNode", crewStr)
                                    self.C.disconnect(cnxns)

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









class HostCreateNode:

        def __init__(self, host, comm):
            self.host = host
            self.con = host.con
            self.address = self.con.fig['addr']
            self.C = comm
            self.H = HashDigest()
            self.crewsToJoin = []

        def sendMessage(self, cnxns, rcvr, tag, msg): #"inviteHostAck"
                sender = self.address
                self.C.sendMessage(self.con, cnxns, sender, rcvr, "createNode", tag, msg)

        def getMessage(self, tag):  #"inviteHost", "createNode"
                return self.C.getMessage(self.con, None, "createNode", tag)
        


        def joinCrewListener(self):
                inviteT = threading.Thread(target=self.invitelistener, args=())
                inviteT.start()
                CNt = threading.Thread(target=self.CNlistener, args=())
                CNt.start()
            
        def invitelistener(self):
                while True:
                        c = self.getMessage("inviteHost")
                        if c != None:                #print(c)
                                msg = c[2]
                                sender = c[0]
                                conn = c[3]
                                print("got invite for new crew from", sender)
                                nodeID = json.loads(msg)[0]
                                parentID = sender[0]
                                if nodeID == parentID+"0" or nodeID == parentID+"1" or (parentID == "root" and (nodeID == "0" or nodeID == "1")):
                                    self.crewsToJoin.append(msg)
                                    #print("accepted new crew req: ", msg)
                                    response = json.dumps([msg, True])
                                    self.sendMessage([conn], sender, "inviteHostAck", response)
                                self.C.disconnect([conn])

        def CNlistener(self):
                while True:
                        c = self.getMessage("createNode")
                        if c != None:
                                msg = c[2]
                                sender = c[0]
                                if msg in self.crewsToJoin:
                                    self.crewsToJoin.remove(msg)
                                    self.createWrkr(msg)
                                conn = c[3]
                                self.C.disconnect([conn])

        def createWrkr(self, nodeInfoString):
                print('Creating worker')
                #get crew stuff
                nodeID = json.loads(nodeInfoString)[0]
                strCrew = json.loads(nodeInfoString)[1]
                Crew = CrewInfo.parse(strCrew)
                #add ID to crewList
                with open(self.con.fig["wrkrlistfile"], "r+") as f:
                    nodeList = f.read()
                    nodeList = nodeList+"\n"+nodeID
                    f.seek(0)
                    f.write(nodeList)
                wrkdir = self.con.fig["wrkrsdir"] + nodeID + "/"
                os.system("mkdir -p " + wrkdir)
                with open(wrkdir + "members.txt", "w") as f:
                    json.dump(Crew,f)
                #start wrkr thread
                self.host.startWrkr(nodeID)



#-------------        
