from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives import serialization 
import os
import json

from HashDigest import HashDigest
from StaticCell import StaticCell
from LedgerCell import LedgerCell
from Cell import Cell, Nucleus
from Procedures import Procedures

class SelectCell:
        
        def __init__(self, wrkr, comm):
                self.wrkr = wrkr
                self.wrkrcon = wrkr.con
                self.members = self.wrkrcon.members
                self.nodeID = self.wrkrcon.nodeID
                self.address = self.wrkrcon.hostcon.fig['addr']
                self.C = comm
                self.H = HashDigest()

        def sendMessage(self, cnxns, rcvr, tag, msg):
                sender = [self.nodeID, self.address]
                self.C.sendMessage(self.wrkrcon, cnxns, sender, rcvr, "selectCell", tag, msg)

        def getMessage(self, tag):
                return self.C.getMessage(self.wrkrcon, None, "selectCell", tag)
        
        def getData(self, cellType, path): #make static data cell
            cell = Cell('')
            if cellType == 'static':
                SC = StaticCell()
                cell = SC.makeStaticCell(path, cell)
                #print(cell.toString())
            elif cellType == 'ledger':
                LC = LedgerCell()
                cell = LC.makeLedgerCell(path, cell)
                #print(cell.toString())
                #run evolution protocol
            self.newCell(cell, 'init')
            #print("select cell result: ", f)

        def newCell(self, cell: Cell, mode):        #mode = 'init'/'resp'
                if mode == 'init':
                        cellString = cell.toString()
                        #share with other crew members -- in crew com
                        cnxns = self.C.connectTo(self.wrkrcon, self.nodeID)
                        evolveOK = True
                        if cnxns != []:
                            self.sendMessage(cnxns, [self.nodeID], 'selectCell', cellString)
                            print("msg sent")
                            #concensus
                            responseSet = self.C.getInCrewResponse(self.wrkrcon, cnxns=None, channel='selectCell', tag='selectCellAck', mode=mode)
                            print("got responses")
                            self.C.disconnect(cnxns)
                            cellHash = self.H.generate(cellString)
                            for resp in responseSet:
                                response = json.loads(resp[2])
                                if response[0] == cellHash and response[1] == False:
                                    evolveOK = False
                                self.C.disconnect([resp[3]])
                        #evolve
                        if evolveOK:
                            flag = Procedures.evolve(self.wrkr, cell)
                            print("evolve result: ", flag)

                elif mode == 'resp':
                        cellString = cell.toString()
                        cellHash = self.H.generate(cellString)
                        response = json.dumps([cellHash, True])
                        print("in select cell response")
                        cnxns = self.C.connectTo(self.wrkrcon, self.nodeID)
                        evolveOK = True
                        if cnxns != []:
                            self.sendMessage(cnxns, [self.nodeID], 'selectCellAck', response)
                            print("sent acknowledgement..")
                            responseSet = self.C.getInCrewResponse(self.wrkrcon, cnxns=None, channel='selectCell', tag='selectCellAck', mode=mode)
                            print("got responses.")
                            self.C.disconnect(cnxns)
                            #print("disconnected")
                            for resp in responseSet:
                                response = json.loads(resp[2])
                                if response[0] == cellHash and response[1] == False:
                                    evolveOK = False
                                self.C.disconnect([resp[3]])
                            #print("out")
                        if evolveOK:
                            flag = Procedures.evolve(self.wrkr, cell)
                            print("evolve result: ", flag)

        def listener(self):
                #if get selectCell req from comm, 
                while True:
                        c = self.getMessage("selectCell")
                        if c != None:                #print(c)
                                print("got new cell")
                                sender = c[0]
                                cellStr = c[2]
                                conn = c[3]
                                if sender[1] in self.members:  #if sender in crew, sign message and send
                                        cell = Cell('')
                                        cell.parse(cellStr)
                                        self.newCell(cell, 'resp')
                                self.C.disconnect([conn])


#----------------------------------

