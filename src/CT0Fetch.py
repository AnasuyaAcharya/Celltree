from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives import serialization 
import os
import json
import threading

from Config import Config, CrewInfo, ClntConfig
#from Communication import ClntCommunication
from Cell import Cell
#from CT0Store import POA
from Config import WrkrConfig


class Fetch:
        
        def __init__(self, wrkr, aux):
            if not isinstance(wrkr, WrkrConfig) and not isinstance(wrkr, Config):
                self.wrkrcon = wrkr.con
                self.C = wrkr.host.comm
                self.St = aux #read only functions
            else:   #wrkrcon and comm passed
                self.wrkrcon = wrkr
                self.C = aux
                self.St = None

        def getCrew(self, nodeID, queryCrewID):                        #client --> crew
                #CrewMems = self.con.getCrewInfo(nodeID)        #dictionary address:pubkey
                cnxns = self.C.connectTo(self.wrkrcon, nodeID)
                if cnxns == None:
                        return None
                self.sendMessage(cnxns, [nodeID], 'fetchCrew', queryCrewID)
                #receive responses
                crew = ""
                while True:         
                        c = self.getMessage("fetchCrewOK")
                        if c != None:
                                #print("response :: ",c)
                                if c[0][0] == nodeID:
                                        crew = c[2]
                                        break
                self.C.disconnect(cnxns)
                if crew != None and crew != '':
                        c = CrewInfo.parse(crew)        #crew mem dictionary
                        return c
                else:
                        return None

        def sendMessage(self, cnxns, rcvr, tag, msg):
                sender = []
                if tag == 'fetchCrewOK' or tag == 'fetchCellOK':
                        sender = [self.wrkrcon.nodeID]
                if tag == 'fetchCrew' or tag == 'fetchCell':
                    if not isinstance(self.wrkrcon, Config):
                        sender = [self.wrkrcon.nodeID, self.wrkrcon.hostcon.fig['addr']]
                    else:
                        sender = self.wrkrcon.fig['addr']
                self.C.sendMessage(self.wrkrcon, cnxns, sender, rcvr, "fetch", tag, msg)

        def getMessage(self, tag = None):
                return self.C.getMessage(self.wrkrcon, None, "fetch", tag)

        def getCellResponse(self, root):                #crew --> client
                print('in get cell response')
                for cell in self.St.poaStore.cellHistory:
                        POA = self.St.poaStore.search(cell, root)
                        #print("POA : ", POA)
                        if POA != None:
                                print(cell, POA)
                                return [cell, POA]
                return None         #no POA found


        def getCrewResponse(self, nodeID):                #crew --> client
                print('in get crew response')
                return self.wrkrcon.getCrewInfo(nodeID)

        def listener(self):                #on crew side
                #if get getCell or getCrew req from comm, 
                tCell = threading.Thread(target=self.FCellListener, args=())
                tCell.start()
                tCrew = threading.Thread(target=self.FCrewListener, args=())
                tCrew.start()
                
        def FCellListener(self):
                while True:
                        c = self.getMessage("fetchCell")
                        print('Got fetchCell request')
                        #print(c)
                        sender = c[0]
                        key = c[2]
                        conn = c[3]
                        response = self.getCellResponse(key)
                        print("response :", response)
                        if response != None:  
                            strRes = json.dumps([response[0].toString(), response[1].toString()])
                            #print(strRes)
                            self.sendMessage([conn], sender, 'fetchCellOK', strRes)
                        else:
                            self.sendMessage([conn], sender, 'fetchCellOK', 'no cell or poa')
                        self.C.disconnect([conn])
                        
        def FCrewListener(self):
                while True:
                        c = self.getMessage('fetchCrew')
                        #print(c)
                        sender = c[0]
                        key = c[2]
                        conn = c[3]
                        response = self.getCrewResponse(key)
                        print("Fetch Crew Response : ", CrewInfo.toString(response))
                        if response != None:  
                            self.sendMessage([conn], sender, 'fetchCrewOK', CrewInfo.toString(response))
                        #print("message sent!")
                        else:
                            pass
                        self.C.disconnect([conn])







class ClntFetch:
        def __init__(self, clntcon, communication): #ClntCommunication):
                self.con = clntcon
                self.C = communication 

        #client crew request response
        def sendMessage(self, cnxns, tag, msg, dest = None):
                self.C.sendMessage(cnxns, "fetch", tag, msg, dest)

        def getMessage(self, cnxns, tag, source = None):
                return self.C.getMessage(cnxns, "fetch", tag, source)

        # Returns a [cell,POA]
        def getCell(self, nodeID, POAroot='root'):                #client --> crew
                #CrewMems = self.con.getCrewInfo(nodeID)        #dictionary address:pubkey
                cnxns = self.C.connectTo(nodeID)  # establish connections with some crew member(s)
                self.sendMessage(cnxns, 'fetchCell', POAroot, dest = [nodeID])
                # return one message if any crew member responds
                cellmsg = self.getMessage(cnxns, 'fetchCellOK', source = [nodeID])  # nodeID for verifying signature
                self.C.disconnect(cnxns)
                return cellmsg[2]

        def getCrew(self, nodeID, queryCrewID):                        #client --> crew
                #CrewMems = self.con.getCrewInfo(nodeID)        #dictionary address:pubkey
                cnxns = self.C.connectTo(nodeID)  # establish connections with some crew member(s)
                if len(cnxns) == 0:
                    raise Exception("Couldn't fetch crew!")

                self.sendMessage(cnxns, 'fetchCrew', queryCrewID, dest = [nodeID])
                #receive responses
                crewmsg = self.getMessage(cnxns, 'fetchCrewOK', source = [nodeID])  # nodeID for verifying signature
                print(crewmsg)
                self.C.disconnect(cnxns)
                return crewmsg[2]

#----------------------------------------------------

