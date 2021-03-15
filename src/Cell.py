import json
import abc

from BankCell import AccountCData, AccountNData, BranchCData, BranchNData
from StaticCell import StaticCData, StaticNData
from LedgerCell import LedgerCData, LedgerNData
from CellInterfaces import EmptyCData, EmptyNData


#---------CELL---------


class Cell:
        nuc = None
        cData = None

        def __init__(self, path):         #path -- file with nuclear data and cell data
                self.nuc = None           
                self.cData = None
                self.readFromFile(path)           

        def toString(self):               #to use in select cell consensus
                sNuc = None
                sCData = None
                if self.nuc != None:
                        sNuc = self.nuc.toString()              
                if self.cData != None:
                        sCData = self.cData.toString()          
                stringCell = {}
                if sNuc != None and sCData != None:
                        stringCell['type'] = self.getType()
                        stringCell['Nuc'] = sNuc
                        stringCell['CData'] = sCData
                        if stringCell['type'] != 'empty':
                                stringCell = json.dumps(stringCell)
                        else:
                                stringCell = ""
                else:
                        stringCell = ""
                return stringCell

        def getType(self):
                if isinstance(self.cData, StaticCData) and isinstance(self.nuc.nData, StaticNData):
                        return 'static'
                elif isinstance(self.cData, LedgerCData) and isinstance(self.nuc.nData, LedgerNData):
                        return 'ledger'
                elif isinstance(self.cData, EmptyCData) and isinstance(self.nuc.nData, EmptyNData):
                        return 'empty' 
                elif isinstance(self.cData, AccountCData) and isinstance(self.nuc.nData, AccountNData):
                        return 'account'
                elif isinstance(self.cData, BranchCData) and isinstance(self.nuc.nData, BranchNData):
                        return 'branch'
                #More cell types

        def parse(self, stringCell: str):      #to execute evolve
                if stringCell != "":
                        stringCell = json.loads(stringCell)
                        self.initCell(stringCell['type'])
                        self.nuc.parse(stringCell['Nuc'])           
                        self.cData.parse(stringCell['CData']) 
                else:
                        self.nuc = Nucleus('')
                        self.nuc.nData = EmptyNData()
                        self.cData = EmptyCData()        

        def initCell(self, CType):
                self.nuc = Nucleus('')
                if CType == 'empty':
                        self.nuc.nData = EmptyNData()
                        self.cData = EmptyCData() 
                elif CType == 'static':
                        self.nuc.nData = StaticNData('')
                        self.cData = StaticCData('')
                elif CType == 'ledger':
                        self.nuc.nData = LedgerNData('')
                        self.cData = LedgerCData('')
                elif CType == 'account':
                        self.nuc.nData = AccountNData('')
                        self.cData = AccountCData('')
                elif CType == 'branch':
                        self.nuc.nData = BranchNData('')
                        self.cData = BranchCData('')
                #More cell types

        def writeToFile(self, path):
                stringCell = self.toString()
                f = open(path,"w")
                f.write(stringCell)
                f.close()
                
        def readFromFile(self, path):
                if path != "":
                        f = open(path,"r")
                        text = f.read()
                        f.close()
                        self.parse(text)         

        def print(self):
            print("Printing Cell ::")
            print("type : ", self.getType())
            if self.nuc != None:
                self.nuc.print()
            else:
                print("nucleus : None")
            if self.cData != None:
                print("cell data : ", self.cData.toString())
            else:
                print("cell data : None")



#---------NUCLEUS-------------


class Nucleus:
        nData = None
        strChkCell = None
        strChkNext = None
        strChkPrev = None

        def __init__(self, string):
                self.parse(string)

        def toString(self):
                #to use for UUList transfer
                if self.nData != None:
                        Ntype = self.getType()
                        if Ntype != 'empty':
                                sNData = self.nData.toString()    
                                stringNuc = {}
                                stringNuc['nData'] = sNData
                                stringNuc['cellType'] = Ntype
                                stringNuc['strChkCell'] = self.strChkCell
                                stringNuc['strChkNext'] = self.strChkNext
                                stringNuc['strChkPrev'] = self.strChkPrev
                                stringNuc = json.dumps(stringNuc)
                                return stringNuc
                        else:
                                return ""
                else:
                        return ""

        def getType(self):
                if isinstance(self.nData, StaticNData):
                        return 'static'
                elif isinstance(self.nData, LedgerNData):
                        return 'ledger'
                elif isinstance(self.nData, EmptyNData):
                        return 'empty' 
                elif isinstance(self.nData, AccountNData):
                        return 'account'
                elif isinstance(self.nData, BranchNData):
                        return 'branch'
                #More cell types
        
        def parse(self, stringNuc: str):
                #to use to execute nuclear codes in rootward, reading
                self.strChkCell = None
                self.strChkNext = None
                self.strChkPrev = None
                if stringNuc != "":
                        stringNuc = json.loads(stringNuc)    
                        CType = stringNuc['cellType']
                        self.initNucData(CType)
                        self.nData.parse(stringNuc['nData'])
                        self.strChkCell = stringNuc['strChkCell']
                        self.strChkNext = stringNuc['strChkNext']
                        self.strChkPrev = stringNuc['strChkPrev']        
                else:
                    self.nData = EmptyNData()

        def initNucData(self, CType):
                if CType == 'empty':
                        self.nData = EmptyNData()
                elif CType == 'static':
                        self.nData = StaticNData('')
                elif CType == 'ledger':
                        self.nData = LedgerNData('')
                elif CType == 'account':
                        self.nData = AccountNData('')
                elif CType == 'branch':
                        self.nData = BranchNData('')
                #More cell types

        def print(self):
            print("Printing Nucleus :: ")
            print("type : ", self.getType())
            if self.nData != None:
                print("nuclear data : ", self.nData.toString())
            else:
                print("nuclear data : None")
            print("check cell code :--")
            print(self.strChkCell)
            print("check next code :--")
            print(self.strChkNext)
            print("check prev code :--")
            print(self.strChkPrev)




#TESTING

#print(cell.toString())
#cell.writeToFile(path)
#print(cell.cData.staticData)
#print(cell.nuc.nData.contentHash)
#print(cell.nuc.strChkCell)
#print(cell.nuc.strChkNext)
#print(cell.nuc.strChkPrev)
#print(cell.nuc.toString())
