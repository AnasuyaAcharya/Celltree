from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives import serialization 
import os
import json

from Config import Config, ClntConfig, CrewInfo, WrkrConfig
from CT0Fetch import Fetch#, ClntFetch




class Discover:

        def __init__(self, wrkrcon, fetch):
                self.wrkrcon = wrkrcon   # can be None, if used by a client (not a host)
                self.root = wrkrcon.getCrewInfo("root")  #address : public key - dictionary
                #print(wrkrcon.fig)
                if isinstance(fetch, Fetch):
                    self.F = fetch#Fetch(wrkrcon, comm)
                else:
                    self.F = Fetch(wrkrcon, fetch)
                self.supervisingLevels = int(wrkrcon.fig['monitoringDepth'])

        def discover(self, nodeID):
                #crewDict - dictionary: nodeID: members(str) for all prefixes of nodeID
                crewDict = {}
                crewDict['root'] = CrewInfo.toString(self.root)
                if nodeID != 'root':
                    crewDict[nodeID] = ''
                while crewDict[nodeID] == '':
                        nodes = list(crewDict.keys())
                        nodes.remove(nodeID)
                        for node in nodes:
                                for i in range(self.supervisingLevels):        #for all prefixes of nodeID after node upto supervising levels:
                                        cID = nodeID[:i+1+len(node)]
                                        if node == 'root':
                                                cID = nodeID[:i+1]
                                        m = self.F.getCrew(node, cID)
                                        if not isinstance(m, str):
                                            m = CrewInfo.toString(m)
                                        if cID not in crewDict or crewDict[cID] == '' :
                                                crewDict[cID] = m        #add to dictionary
                                                #write new members to file
                                                path = ""
                                                if isinstance(self.wrkrcon, WrkrConfig):
                                                    path = self.wrkrcon.hostcon.fig['crewsdir']+cID
                                                else:
                                                    path = self.wrkrcon.fig['crewsdir']+cID
                                                CrewInfo.write(path, m)
                                        else:
                                                if crewDict[cID] != m:
                                                        print('Warning: Discovery error: crew mis-match')
                                        if cID == nodeID:
                                            return crewDict[nodeID]
                return crewDict[nodeID]

        def discoverFetch(self, nodeID, rootID):
                mem = self.wrkrcon.getCrewInfo(nodeID)
                if mem == None:
                        text = self.discover(nodeID)
                        crewMembers = CrewInfo.parse(text)
                        return [crewMembers, self.root]
                else:
                        return [mem, self.root]



class ClntDiscover:

        def __init__(self, clntcon, fetch):
                self.con = clntcon   
                self.fetch = fetch
                self.root = clntcon.getCrewInfo("root")  #address : public key - dictionary
                self.supervisingLevels = int(clntcon.fig['monitoringDepth'])

        def discover(self, nodeID):
                #crewDict - dictionary: nodeID: members(str) for all prefixes of nodeID
                crewDict = {}
                crewDict['root'] = CrewInfo.toString(self.root)
                if nodeID != 'root':
                        crewDict[nodeID] = ''
                while crewDict[nodeID] == '':
                        nodes = list(crewDict.keys())
                        nodes.remove(nodeID)
                        for node in nodes:
                                for i in range(self.supervisingLevels):        #for all prefixes of nodeID after node upto supervising levels:
                                        cID = nodeID[:i+1+len(node)]
                                        if node == 'root':
                                                cID = nodeID[:i+1]
                                        #print(cID)
                                        m = self.fetch.getCrew(node, cID)
                                        #print("get crew response : ",m)
                                        if not isinstance(m, str):
                                            m = CrewInfo.toString(m)
                                        if cID not in crewDict or crewDict[cID] == '' :
                                                crewDict[cID] = m        #add to dictionary
                                                #write new members to file
                                                path = self.con.fig['crewsdir']+cID
                                                CrewInfo.write(path, m)
                                        else:
                                                if crewDict[cID] != m:
                                                        print('Warning: Discovery error: crew mis-match')
                                        if cID == nodeID:
                                            return crewDict[nodeID]
                return crewDict[nodeID]

        def discoverFetch(self, nodeID, rootID):
                mem = self.con.getCrewInfo(nodeID)
                if mem == None:
                        text = self.discover(nodeID)
                        crewMembers = CrewInfo.parse(text)
                        return [crewMembers, self.root]
                else:
                        return [mem, self.root]

#-------------------------------------------------
