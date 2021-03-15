import json

from Cell import Cell, Nucleus
from CrewSign import CrewSign, ClntSign
from Config import WrkrConfig


class Store:
        currentCell = None
        uuList = None #list of nuc
        mmTree = None #dictionary of nodes
        poaStore = None #dictionary cell:poa
        #assimData = None  #list of uulists + subtree hashes

        def __init__(self, wrkrcon):
                self.wrkrcon = wrkrcon
                self.uuList = UUList()                        #DONE!!! -- no file storage
                self.mmTree = MerkleMultiTree(wrkrcon) #includes pointer to latest mTree root
                self.poaStore = POAStore(wrkrcon)
                path = self.wrkrcon.fig['files']['cell']
                self.currentCell = Cell(path)
        
        def updateCell(self, cell):        #EVOLVE uses
                self.currentCell = cell        #cell object
                path = self.wrkrcon.fig['files']['cell']
                self.currentCell.writeToFile(path)

        def listener(self):
                pass


                
class UUList:
        uuList = None

        def __init__(self):
                self.uuList = []

        def add(self, nuc):           #class Nucleus
                if isinstance(nuc, Nucleus):
                        self.uuList.append(nuc)

        def flush(self):
                temp = self.uuList
                self.uuList = []
                return temp

        def toString(self):           #to send UUList for rootward 
                stringUUList = [] 
                for nuc in self.uuList:
                        stringUUList.append(nuc.toString())
                stringUUList = json.dumps(stringUUList)
                return stringUUList

        def parse(self, stringUUList):#to get UUList for consistancy checks in rootward
                self.uuList = []
                stringUUList = json.loads(stringUUList)
                for n in stringUUList:
                        nuc = Nucleus("")
                        nuc.parse(n)
                        self.uuList.append(nuc)

        #NO NEED FOR FILE STORAGE FOR UULIST



#TESTING
#uuList = UUList()
#print(uuList.toString())

#from StaticCell import Cell, Nucleus
#path = "Cells/1.txt"
#cell = Cell(path)
#uuList.add(cell.nuc)
#print(uuList.toString())
#print(uuList.uuList)

#uuList.add(cell.nuc)
#print(uuList.toString())
#print(uuList.uuList)

#uuList.parse(uuList.toString())
#print(uuList.uuList)

#print(uuList.flush())
#print(uuList.uuList)




class MerkleMultiTree:
        nodeDict = None
        lastRoot = None #cumulative hash key of latest root of mmtree
        
        def __init__(self, wrkrcon):
                self.wrkrcon = wrkrcon
                self.nodeID = wrkrcon.nodeID
                self.H = wrkrcon.hasher
                self.path = self.wrkrcon.fig['files']['mmtree']
                #read mmtree elements from file
                self.readFromFile("")

        def getCumulativeHash(self, node):    #MNode
                cuHash = self.H.getCumulativeHash(node)
                return cuHash

        def parse(self, stringTData: str):
                self.nodeDict = {}
                if stringTData != "":
                        data = json.loads(stringTData)
                        self.lastRoot = data['lastRoot']
                        for cuHash in data:
                                if cuHash != 'lastRoot':
                                        node = MNode(None, None, None, "","")
                                        node.parse(data[cuHash])
                                        self.nodeDict[cuHash] = node

        def writeToFile(self, path):
                textTree = self.toString()      
                if path == "":
                        path = self.path
                f = open(path,"w")
                f.write(textTree)
                f.close()
                
        def readFromFile(self, path):
                #read mmtree elements from file
                if path == "":
                        path = self.path
                f = open(path,"r")
                textTree = f.read()
                f.close()
                self.parse(textTree)

        def toString(self):
                if len(self.nodeDict) != 0:
                        stringMMT = {}
                        for node in self.nodeDict:
                                stringMMT[node] = self.nodeDict[node].toString()
                        stringMMT['lastRoot'] = self.lastRoot
                        stringMMT = json.dumps(stringMMT)
                        return stringMMT
                else:
                        return ""

        def updateMMTree(self, listOfNodes):     #mTree with current node as root: list(not dict)
                for node in listOfNodes:
                        cuHash = self.getCumulativeHash(node)
                        self.nodeDict[cuHash] = node
                        if node.nodeID == self.nodeID:    #update latest root
                                self.lastRoot = cuHash

        def cleanMMTree(self, rootNodeList):      #list of roots hashes to be removed
                #remove obsolete versions of this node
                for node in rootNodeList:
                        keys = []
                        for n in self.nodeDict.keys():
                                keys.append(n)
                        for nx in keys:
                                if node == nx:
                                        del self.nodeDict[nx]
                self.collectGarbage()

        def collectGarbage(self):
                ctr = 0
                keys = [] 
                for i in self.nodeDict.keys():
                        keys.append(i)
                for nodeHash in keys:
                        flag = False
                        keys1 = []
                        for j in self.nodeDict.keys():
                                keys1.append(j)
                        for node in keys1:
                                if self.nodeDict[node].rChildCuHash == nodeHash:
                                        flag = True
                                if self.nodeDict[node].lChildCuHash == nodeHash:
                                        flag = True
                                if self.nodeDict[nodeHash].nodeID == self.nodeID:
                                        flag = True
                        if flag == False:
                                del self.nodeDict[nodeHash]
                                ctr = ctr + 1
                if ctr > 0:
                        self.collectGarbage()

        def getTree(self, leaves, nodeID, POA): #POA.merklePath dictionary cuHash:node        #nodeID--root from which tree is to be returned         #leaves = 0,1 only    LEAFWARD
                if POA != None and POA != "":                #NEED TO TEST WITH POA!!
                        #find last node in POA.merklePath --- node with nodeID = nodeID
                        node = None
                        for n in POA.merklePath:
                                if POA.merklePath[n].nodeID == nodeID:
                                        node = n
                                        break
                        if node != None and node in self.nodeDict.keys():
                                #find dictionary elements with node as root upto 0,1 only
                                mTree = {}
                                #cuHash = self.getCumulativeHash(node)
                                mTree[node] = self.nodeDict[node]
                                try:
                                    mTree[self.nodeDict[node].lChildCuHash] = self.nodeDict[self.nodeDict[node].lChildCuHash]
                                except:
                                    pass
                                    #print("getTree : left child not found")
                                try:
                                    mTree[self.nodeDict[node].rChildCuHash] = self.nodeDict[self.nodeDict[node].rChildCuHash]
                                except:
                                    pass
                                    #print("getTree : right child not found")
                                return mTree
                        return None
                else:
                        #find from nodeDict latest node of nodeID
                        #print("IN!!")
                        try:
                                n = self.nodeDict[self.lastRoot]
                                while n.nodeID != nodeID:
                                        if nodeID[len(n.nodeID)] == '0':
                                                n = self.nodeDict[n.lChildCuHash]
                                        elif nodeID[len(n.nodeID)] == '1':
                                                n = self.nodeDict[n.rChildCuHash]
                                #print(n.toString())
                                #add root node to mTree dictionary
                                mTree = {}
                                cuHash = self.getCumulativeHash(n)
                                mTree[cuHash] = n
                                #add all nodes till leaf in mTree
                                hashlist = [cuHash]
                                while len(hashlist) > 0:
                                        h = hashlist[0]
                                        for leaf in leaves: #if left child within subtree
                                                try:
                                                        if leaf.startswith(self.nodeDict[self.nodeDict[h].lChildCuHash].nodeID):
                                                                mTree[self.nodeDict[h].lChildCuHash] = self.nodeDict[self.nodeDict[h].lChildCuHash]
                                                                hashlist.append(self.nodeDict[h].lChildCuHash)
                                                                break
                                                except:
                                                        pass
                                        for leaf in leaves: #if right child within subtree
                                                try:
                                                        if leaf.startswith(self.nodeDict[self.nodeDict[h].rChildCuHash].nodeID):
                                                                mTree[self.nodeDict[h].rChildCuHash] = self.nodeDict[self.nodeDict[h].rChildCuHash]
                                                                hashlist.append(self.nodeDict[h].rChildCuHash)
                                                                break
                                                except:
                                                        pass
                                        hashlist.remove(h)
                                return mTree
                        except:
                                return None

        def concat(self, mTree1, mTree2):  #node at end of tree1 = root of tree2, tree1 and tree2 are dictionaries
                fulltree = mTree1
                node = None
                for n1 in mTree1:   #find common node
                        for n2 in mTree2:
                                if n1 == n2:
                                        node = n1
                                        break
                        if node != None:
                                break
                for n in mTree2:
                        if n != node:
                                #cuHash = self.getCumulativeHash(n)
                                #fulltree[cuHash] = n
                                fulltree[n] = mTree2[n]
                if node != None:
                        return fulltree
                else:
                        return None



class MNode:
        nodeID = None
        nuc = None
        nonce = None
        rChildCuHash = ""
        lChildCuHash = ""

        def __init__(self, nodeID, nuc, nonce, lPtr, rPtr):      #Nucleus, nonce, hash, hash
                #self.wrkrcon = wrkrcon
                self.nodeID = nodeID
                self.nuc = nuc
                self.nonce = nonce
                self.lChildCuHash = lPtr
                self.rChildCuHash = rPtr

        def updateL(self, lPtr):
                self.lChildCuHash = lPtr

        def updateR(self, rPtr):
                self.rChildCuHash = rPtr

        def toString(self):
                strNode = {}
                strNode['nodeID'] = self.nodeID
                strNode['nuc'] = ""
                if self.nuc != None:
                        strNode['nuc'] = self.nuc.toString()
                strNode['nonce'] = self.nonce
                strNode['lChildCuHash'] = self.lChildCuHash
                strNode['rChildCuHash'] = self.rChildCuHash
                strNode = json.dumps(strNode)
                return strNode

        def parse(self, strNode: str):
                #print("parse:  ", strNode)
                if strNode != "":
                        strNode = json.loads(strNode)
                        self.nodeID = strNode['nodeID']
                        self.nuc = Nucleus("")
                        self.nuc.parse(strNode['nuc'])
                        self.nonce = strNode['nonce']
                        self.lChildCuHash = strNode['lChildCuHash']
                        self.rChildCuHash = strNode['rChildCuHash']




class AssimData:        #assim signal of whole subtree      
        #UUList, MNode for all monitored nodes -- dictionary nodeID:[MNode,UUList]
        AssimSignalDict = None
        path = None

        def __init__(self, wrkrcon):  
                self.AssimSignalDict = {}
                self.wrkrcon = wrkrcon
                self.path = self.wrkrcon.fig['files']['assimData']
                self.CS = CrewSign(wrkrcon, None)
                self.readFromFile()

        def readFromFile(self, path=None):
                if path is None:
                        path = self.path
                text = ""
                with open(path,"r") as f:
                        text = f.read()
                self.parse(text)

        def writeToFile(self, path=None):          
                if path is None:
                        path = self.path
                text = self.toString()      
                with open(path,"w") as f:
                        f.write(text)

        def toString(self):
                if len(self.AssimSignalDict) != 0:
                        text = {}        
                        for nodeID in self.AssimSignalDict:
                                textnode = self.AssimSignalDict[nodeID][0].toString()
                                textUUlist = self.AssimSignalDict[nodeID][1].toString()
                                textSign = self.CS.toString(self.AssimSignalDict[nodeID][2])
                                text[nodeID] = json.dumps([textnode, textUUlist, textSign])
                        text = json.dumps(text)
                        return text
                else:
                        return ""

        def verifyAssimData(self, sign, uuList, mNode, nodeID):
            if sign == None:
                return False
            text = ""
            textnode = mNode
            if not isinstance(mNode, str):
                textnode = mNode.toString()
            textUUlist = uuList
            if not isinstance(uuList, str):
                textUUlist = uuList.toString()
            text = json.dumps([textnode, textUUlist])
            return self.CS.verify([nodeID], text, sign)


        def parse(self, text: str):
                if text != "":
                        text = json.loads(text)
                        self.AssimSignalDict = {}
                        for nodeID in text:
                                s = json.loads(text[nodeID])
                                node = MNode(None,None,None,"","")
                                node.parse(s[0])
                                uulist = UUList()
                                uulist.parse(s[1])
                                sign = self.CS.parse(s[2])
                                self.AssimSignalDict[nodeID] = [node,uulist,sign]

        def update(self, newData):      
                self.parse(newData)
                self.writeToFile()

        def append(self, text):      
                if text != "":
                        #print("assim data to parse:: ", text)
                        text = json.loads(text)
                        for nodeID in text:
                                s = json.loads(text[nodeID])
                                node = MNode(None,None,None,"","")
                                node.parse(s[0])
                                uulist = UUList()
                                uulist.parse(s[1])
                                sign = self.CS.parse(s[2])
                                self.AssimSignalDict[nodeID] = [node,uulist,sign]




#TESTING
"""AD = AssimData('1')

uul = UUList()
uul.add(cell.nuc)
uul.add(cell.nuc)
AD.AssimSignalDict["1"] = [node1, uul]
AD.AssimSignalDict["10"] = [node10, uul]
AD.AssimSignalDict["11"] = [node11, uul]
str = AD.toString()

AD.update(str)"""




#POA.merklePath dictionary cuHash:node

class POA:
        merklePath = None   #dictionary cuHash:node
        sign = None         #CrewSign on MNode.toString()
        wrkrcon = None     #used to find public keys for verification

        def __init__(self, merklePath, sign, wrkrcon):
                self.merklePath = merklePath
                self.sign = sign
                self.wrkrcon = wrkrcon
                if type(wrkrcon) == WrkrConfig:
                        self.S = CrewSign(wrkrcon, None)        #used only for verification
                else:
                        self.S = ClntSign(wrkrcon)
                self.H = wrkrcon.hasher
                if self.checkPOA() == False:
                        #print("check POA False")
                        self.merklePath = None
                        self.sign = None
                #print(self.checkPOA())

        def checkPOA(self):
                if self.merklePath is None or self.sign is None:
                        return False
                #check if POA is merkle path
                merklePathList = []
                #for n in self.merklePath:
                        #merklePathList.append(self.merklePath[n])
                rootHash = self.H.mEval(self.merklePath)#List)
                #print(rootHash)
                if rootHash != 'invalid':
                        #check if signed node is POAroot
                        message = self.merklePath[rootHash].toString()
                        #print("POA signed: ", message)
                        #check if sign verifies
                        return self.S.verify(['root'], message, self.sign)
                return False

        def toString(self):
            if self.sign != None and self.merklePath != None:
                stringSign = self.S.toString(self.sign)
                stringMPath = {}
                for h in self.merklePath:
                        sNode = self.merklePath[h].toString()
                        stringMPath[h] = sNode
                stringMPath = json.dumps(stringMPath)
                stringPOA = json.dumps([stringSign, stringMPath])
                return stringPOA
            else:
                return "None"

        def merklePathStr(self):
            if self.merklePath == None:
                return "None"
            else:
                stringMPath = {}
                for h in self.merklePath:
                    sNode = self.merklePath[h].toString()
                    stringMPath[h] = sNode
                stringMPath = json.dumps(stringMPath)
                return stringMPath

        def parse(self, stringPOA):
            if stringPOA != "None":
                stringPOA = json.loads(stringPOA)
                stringSign = stringPOA[0]
                stringMPath = stringPOA[1]
                self.sign = self.S.parse(stringSign)                            
                self.merklePath = {}
                stringMPath = json.loads(stringMPath)
                for s in stringMPath:
                        node = MNode(None, None, None, "", "")
                        node.parse(stringMPath[s])
                        h = self.H.getCumulativeHash(node)                                                
                        self.merklePath[h] = node
                if self.merklePath != None and self.sign != None:
                        if self.checkPOA() == False:
                                self.merklePath = None
                                self.sign = None
                        return
            self.merklePath = None
            self.sign = None

        def printPOApath(self):
            print("POA merkle node list : ")
            for h in self.merklePath:
                print("cumulative hash : ", h, " -- nodeID : ", self.merklePath[h].nodeID )




class POAStore:
        cellHistory = None #dictionary -- cell:[(rootID,POA)]

        def __init__(self, wrkrcon):
                self.wrkrcon = wrkrcon
                path = self.wrkrcon.fig['files']['poaStore']
                self.readFromFile(path)
                self.nodeID = wrkrcon.nodeID

        def readFromFile(self, path):
                if path != "":
                        f = open(path,"r")
                        text = f.read()
                        f.close()
                        self.parse(text)

        def writeToFile(self):
                text = self.toString()      
                f = open(path,"w")
                f.write(text)
                f.close()

        def toString(self):
                stringPOAData = {}
                for cell in self.cellHistory:
                        stringCell = cell.toString()
                        stringPOAList = []
                        for i in self.cellHistory[cell]:
                                stringRoot = i[0]
                                stringPOA = i[1].toString()
                                stringPOAList.append(json.dumps([stringRoot, stringPOA]))
                        stringPOAList = json.dumps(stringPOAList)
                        stringPOAData[stringCell] = stringPOAList
                stringPOAData = json.dumps(stringPOAData)
                return stringPOAData

        def parse(self, stringPOAData):
                self.cellHistory = {}
                if stringPOAData != "":
                        stringPOAData = json.loads(stringPOAData)
                        for cellstr in stringPOAData:
                                cell = Cell("")
                                cell.parse(cellstr)
                                self.cellHistory[cell] = []
                                stringPOAlist = json.loads(stringPOAData[cellstr])
                                for i in stringPOAlist:
                                        i = json.loads(i)
                                        root = i[0]
                                        poa = POA(None, None, self.wrkrcon)
                                        poa.parse(i[1])
                                        self.cellHistory[cell].append([root,poa])

        def add(self, cell, root, POA):
                if type(cell) == str:
                        c = Cell("")
                        c.parse(cell)
                        cell = c
                if type(POA) == str:
                        p = POA(None,None, self.wrkrcon)
                        p.parse(POA)
                        POA = p
                if cell in self.cellHistory.keys():
                        #self.cellHistory[cell].append([root,POA])
                        self.addPOA(root, POA)
                else:
                        self.addCell(cell)
                        self.addPOA(root, POA)
                        #self.cellHistory[cell].append([root,POA])

        def addCell(self, cell):
                if type(cell) == str:
                        c = Cell("")
                        c.parse(cell)
                        cell = c
                self.cellHistory[cell] = []

        def addPOA(self, root, POA):
                if type(POA) == str:
                        p = POA(None, None, self.wrkrcon)
                        p.parse(POA)
                        POA = p
                #for CT0 only!!
                for cell in self.cellHistory:
                    nuc = cell.nuc
                    mPath = POA.merklePath
                    flag = False
                    if (len(mPath) == len(self.nodeID)+1) or (self.nodeID == 'root' and len(mPath)==1):
                        for h in mPath:
                            if mPath[h].nuc.toString() == nuc.toString() and mPath[h].nodeID == self.nodeID:
                                flag = True
                    if flag:
                        self.cellHistory[cell] = [[root, POA]]
                        print("POA added to cell history")
                        break
                #print("cell History: ", self.cellHistory)

        def delete(self, cell):
                if type(cell) == str:
                        c = Cell("")
                        c.parse(cell)
                        cell = c
                for c in self.cellHistory:
                        if c.toString() == cell.toString():
                                return self.cellHistory.pop(c)
                return None

        def exists(self, cell, root, POA):
                if type(cell) == str:
                        c = Cell("")
                        c.parse(cell)
                        cell = c
                if type(POA) == str:
                        p = POA(None,None, self.wrkrcon)
                        p.parse(POA)
                        POA = p
                for c in self.cellHistory:
                        if c.toString() == cell.toString():
                                flag = False
                                for element in self.cellHistory[c]:
                                        if element[0] == root and element[1].toString() == POA.toString():
                                                flag = True
                                                break
                                return flag
                return False

        def search(self, cell, root):
                if type(cell) == str:
                        c = Cell("")
                        c.parse(cell)
                        cell = c
                #print("search cell history ", self.cellHistory)
                for c in self.cellHistory:
                        if c.toString() == cell.toString():
                                for element in self.cellHistory[c]:
                                        if element[0] == root:
                                                POA = element[1]
                                                return POA
                return None


##TESTING
"""poas = POAStore("1")
poas.cellHistory[cell] = [["ROOT", poa]]

poas.add(cell, "ROOT", poa)
print(poas.exists(cell, "ROOT", poa))

strpoa = poas.toString()
print(strpoa)
poas.parse(strpoa)

poas.delete(cell)
poas.add(cell, "ROOT", poa)
epoa = poas.search(cell, "ROOT")
print("EXISTS::", epoa)
"""
