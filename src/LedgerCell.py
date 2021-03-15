import json
#import abc

from CellInterfaces import CellData, NuclearData
from HashDigest import HashDigest
#static data cell - opcodes python

class LedgerCell:

        def __init__(self):
                self.H = HashDigest()

        def makeLedgerCell(self, path, cell):
                #read cell data
                f = open(path, "r")
                text = f.read()
                f.close()
                #make ledger cell
                cell.initCell('ledger')
                cell.cData.setBlockArray(text)
                self.makeNData(cell)
                #h = self.H.generate(text)
                #cell.nuc.nData.setContentHash(h)
                strChkCell = """

def checkCell(cellString):
        cell = Cell("")
        cell.parse(cellString)
        h = HashDigest()
        blocks = cell.cData.getBlockArray()
        n = len(blocks)
        if n == cell.nuc.nData.getChainLength():
                BH = h.generate(blocks[n-1])
                CH = ''
                if n == 1:
                        CH = h.generate(blocks[0])
                else:
                        CH = h.generate(h.generate(blocks[0])+h.generate(blocks[1]))
                for i in range(n):
                        if i > 1:
                                bh = h.generate(blocks[i])
                                CH = h.generate(CH+bh)
                if CH == cell.nuc.nData.getChainHash() and BH == cell.nuc.nData.getLastBlockHash():
                        return True
        return False

"""
                strChkNext = """

def checkNext( nucStr, nucNStr):
        nuc = Nucleus("")
        nuc.parse(nucStr)
        nucN = Nucleus("")
        nucN.parse(nucNStr)
        h = HashDigest()
        if isinstance(nuc.nData, EmptyNData):
                if nucN.nData.getChainLength() == 1 and nucN.nData.getChainHash() == nucN.nData.getLastBlockHash():
                        return True
                else:
                        return False
        else:
                if nucN.nData.getChainLength() != nuc.nData.getChainLength()+1:
                        return False
                if nucN.nData.getChainHash() != h.generate(nuc.nData.getChainHash()+nucN.nData.getLastBlockHash()):
                        return False
                if nuc.strChkCell != nucN.strChkCell or nuc.strChkNext != nucN.strChkNext or nuc.strChkPrev != nucN.strChkPrev:
                        return False
                return True

"""
                strChkPrev = """

def checkPrevious( nucStr, nucPStr):
        nuc = Nucleus("")
        nuc.parse(nucStr)
        nucP = Nucleus("")
        nucP.parse(nucPStr)
        #print("prev nuc : ", nucP.toString())
        #print("next nuc : ", nuc.toString())
        h = HashDigest()
        #print(type(nucP.nData))
        #print(type(nuc.nData))
        if isinstance(nucP.nData, EmptyNData):
                print("in empty prev nuc case")
                if nuc.nData.getChainLength() == 1 and nuc.nData.getChainHash() == nuc.nData.getLastBlockHash():
                        return True
                else:
                        return False
        else:
                if nuc.nData.getChainLength() != nucP.nData.getChainLength()+1:
                        return False
                if nuc.nData.getChainHash() != h.generate(nucP.nData.getChainHash()+nuc.nData.getLastBlockHash()):
                        return False
                if nuc.strChkCell != nucP.strChkCell or nuc.strChkNext != nucP.strChkNext or nuc.strChkPrev != nucP.strChkPrev:
                        return False
                return True

"""
                cell.nuc.strChkCell = strChkCell
                cell.nuc.strChkNext = strChkNext
                cell.nuc.strChkPrev = strChkPrev
                return cell

        def makeNData(self, cell):
                blocks = cell.cData.getBlockArray()
                n = len(blocks)
                cell.nuc.nData.setChainLength(n)
                BH = self.H.generate(blocks[n-1])
                CH = ''
                if n == 1:
                        CH = self.H.generate(blocks[0])
                else:
                        CH = self.H.generate(self.H.generate(blocks[0])+self.H.generate(blocks[1]))
                for i in range(n):
                        if i > 1:
                                bh = self.H.generate(blocks[i])
                                CH = self.H.generate(CH+bh)
                cell.nuc.nData.setChainHash(CH)
                cell.nuc.nData.setLastBlockHash(BH)





###-------CELL DATA---------

class LedgerCData(CellData):
        Data = None

        def __init__(self, string: str):
                #self.parse(string)
                self.Data = {}

        def toString(self):
                return json.dumps(self.Data)

        def parse(self, stringData: str):
                self.Data = json.loads(stringData)

        def getBlockArray(self):
                return self.Data['blockArray']

        def setBlockArray(self, data):
                if isinstance(data, str):
                        data = json.loads(data)
                self.Data['blockArray'] = data  #array


#------NUCLEAR DATA-----------


class LedgerNData(NuclearData):
        Data = None

        def __init__(self, string: str):
                #self.parse(string)
                self.Data = {}

        def toString(self):
                return json.dumps(self.Data)

        def parse(self, stringData: str):
                self.Data = json.loads(stringData)

        def getChainLength(self):
                return self.Data['chainLength']

        def setChainLength(self, n: int):
                self.Data['chainLength'] = n

        def getLastBlockHash(self):
                return self.Data['lastBlockHash']

        def setLastBlockHash(self, data: str):
                self.Data['lastBlockHash'] = data

        def getChainHash(self):
                return self.Data['chainHash']

        def setChainHash(self, data: str):
                self.Data['chainHash'] = data








#TESTING


#print(cell.toString())
#cell.writeToFile(path)
#print(cell.cData.staticData)
#print(cell.nuc.nData.contentHash)
#print(cell.nuc.strChkCell)
#print(cell.nuc.strChkNext)
#print(cell.nuc.strChkPrev)
#print(cell.nuc.toString())
