import json
#import abc

from CellInterfaces import CellData, NuclearData
from HashDigest import HashDigest
#static data cell - opcodes python

class StaticCell:

        def __init__(self):
                self.H = HashDigest()

        def makeStaticCell(self, path, cell):
                #read cell data
                f = open(path, "r")
                text = f.read()
                f.close()
                #make static cell
                #cell = Cell('')
                cell.initCell('static')
                cell.cData.setCellData(text)
                h = self.H.generate(text)
                cell.nuc.nData.setContentHash(h)
                strChkCell = """

def checkCell(cellString):
        cell = Cell("")
        cell.parse(cellString)
        h = HashDigest()
        hash = h.generate(cell.cData.Data['cellData'])
        if str(hash) == cell.nuc.nData.Data['contentHash']:
                return True
        else:
                return False
"""
                strChkNext = """

def checkNext( nucStr, nucNStr):
        #print("check next")
        #print("nuc str: ", nucStr)
        #print("nuc new str: ", nucNStr)
        if nucStr != "":
                return False
        else:
                if nucNStr != None:
                        return True
                else:
                        return False
"""
                strChkPrev = """

def checkPrevious( nucStr, nucPStr):
        #print("check prev")
        #print("nuc str: ", nucStr)
        #print("nuc prev str:", nucPStr)
        if nucStr == nucPStr:
                return True
        else:
                if nucPStr == "":
                        return True
                else:
                        return False
"""
                cell.nuc.strChkCell = strChkCell
                cell.nuc.strChkNext = strChkNext
                cell.nuc.strChkPrev = strChkPrev
                return cell







###-------CELL DATA---------

class StaticCData(CellData):
        Data = None

        def __init__(self, string: str):
                #self.parse(string)
                self.Data = {}

        def toString(self):
                return json.dumps(self.Data)

        def parse(self, stringData: str):
                self.Data = json.loads(stringData)

        def getCellData(self):
                return self.Data['cellData']

        def setCellData(self, data: str):
                self.Data['cellData'] = data


#------NUCLEAR DATA-----------


class StaticNData(NuclearData):
        Data = None

        def __init__(self, string: str):
                #self.parse(string)
                self.Data = {}

        def toString(self):
                return json.dumps(self.Data)

        def parse(self, stringData: str):
                self.Data = json.loads(stringData)

        def getContentHash(self):
                return self.Data['contentHash']

        def setContentHash(self, data: str):
                self.Data['contentHash'] = data








#TESTING


#print(cell.toString())
#cell.writeToFile(path)
#print(cell.cData.staticData)
#print(cell.nuc.nData.contentHash)
#print(cell.nuc.strChkCell)
#print(cell.nuc.strChkNext)
#print(cell.nuc.strChkPrev)
#print(cell.nuc.toString())
