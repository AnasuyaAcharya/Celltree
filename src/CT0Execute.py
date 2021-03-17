from RestrictedPython import compile_restricted
import os
import json

from Cell import Cell, Nucleus
from HashDigest import HashDigest
from StaticCell import StaticCData, StaticNData
from LedgerCell import LedgerCData, LedgerNData
from CellInterfaces import EmptyCData, EmptyNData

class Execute:
        
        def __init__(self):
                # initialize run time environment
                pass

        def exe(self, tag, strCode, ArgsArray):
                #extract arguements from ArgsArray
                #pass arguements as string
                #empty code:
                if strCode == '' or strCode == None:
                        if tag == "chkCell":
                                return True
                        if tag == "chkPrev":
                                return False
                        if tag == "chkNext":
                                return True
                #compile code
                byte_code = compile(strCode, filename = '<inline code>', mode='exec')
                lcls = {}
                exec(byte_code, None, lcls)
                for name, value in lcls.items():
                        setattr(self, name, value)
                #run nuclear codes
                #print(strCode)
                try:
                        if tag == "chkCell":
                                cell = ArgsArray[0]
                                ans = self.checkCell(cell)
                                print("chkCell")
                                return ans
                        if tag == "chkPrev":
                                nuc = ArgsArray[0]
                                nucP = ArgsArray[1]
                                ans = self.checkPrevious(nuc, nucP)
                                print("chkPrev")
                                return ans
                        if tag == "chkNext":
                                nuc = ArgsArray[0]
                                nucN = ArgsArray[1]
                                ans = self.checkNext(nuc, nucN)
                                print("chkNext")
                                return ans
                except:
                        print("except exe ", tag)
                        return False


#-------------------------------------------------
