import json
#import abc

from CellInterfaces import CellData, NuclearData
from HashDigest import HashDigest
#static data cell - opcodes python



class Transaction:
    txn = None

    def __init__(self):
        self.H = HashDigest()
        
    def createNew(amount, sender, receiver, sEpoch, rEpoch, tag, nonce=None, isWithdrawal=False, isDeposit=False, branchSign=None): #tag = 'init' / 'resp'
        self.txn['amount'] = amount
        self.txn['sender'] = sender
        self.txn['receiver'] = receiver
        self.txn['senderEpoch'] = sEpoch
        self.txn['receiverEpoch'] = rEpoch
        if nonce != None:
            self.txn['nonce'] = nonce
        else:
            self.txn['nonce'] = self.H.generateNonce()
        self.txn['isWithdrawal'] = isWithdrawal
        self.txn['isDeposit'] = isDeposit
        self.txn['branchSign'] = branchSign
        self.txn['tag'] = tag
        self.txn['txnID'] = self.getTxnID()

    def toString(self):
        if self.txn != None:
            return json.dumps(self.txn)

    def parse(strTxn):
        self.txn = json.loads(strTxn)


    def getTxnID(self):
        if self.txn != None:
            dataToHash = {}
            for k in self.txn:
                if k != 'txnID' and k != 'tag':
                    dataToHash[k] = self.txn[k]
            strTxn = json.dumps(dataToHash)
            txnID = self.H.generate(strTxn)
            return txnID
        else:
            return None

    def isValid(self):
        if 'amount' not in self.txn:
            return False
        if 'sender' not in self.txn:
            return False
        if 'receiver' not in self.txn:
            return False
        if 'senderEpoch' not in self.txn:
            return False
        if 'receiverEpoch' not in self.txn:
            return False
        if 'nonce' not in self.txn:
            return False
        if self.txn['nonce'] == None:
            return False
        if 'isWithdrawal' not in self.txn:
            return False
        if 'isDeposit' not in self.txn:
            return False
        if 'branchSign' not in self.txn:
            return False
        if self.txn['isWithdrawal']:
            if self.txn['isDeposit']:
                return False
            if self.txn['branchSign'] == None:
                return False
        if self.txn['isDeposit']:
            if self.txn['isWithdrawal']:
                return False
            if self.txn['branchSign'] == None:
                return False
        if 'tag' not in self.txn:
            return False
        if self.txn['tag'] != 'init' and self.txn['tag'] != 'resp':
            return False
        if 'txnID' not in self.txn:
            return False
        if self.txn['txnID'] != self.getTxnID():
            return False
        return True

    def getSender(self):
        return self.txn['sender']

    def isSender(self, nodeID):
        if self.txn['sender'] == nodeID:
            return True
        return False

    def getReceiver(self):
        return self.txn['receiver']

    def isReceiver(self, nodeID):
        if self.txn['receiver'] == nodeID:
            return True
        return False

    def getAmount(self):
        return self.txn['amount']

    def isInitiator(self):
        if self.txn['tag'] == 'init':
            return True
        else:
            return False

    def isResponder(self):
        if self.txn['tag'] == 'resp':
            return True
        else:
            return False

    def getInitiator(self, nodeID):
        if self.txn['tag'] == 'init':
            return nodeID
        else:
            if self.txn['sender'] == nodeID:
                return self.txn['receiver']
            if self.txn['receiver'] == nodeID:
                return self.txn['sender']

    def getResponder(self, nodeID):
        if self.txn['tag'] == 'resp':
            return nodeID
        else:
            if self.txn['sender'] == nodeID:
                return self.txn['receiver']
            if self.txn['receiver'] == nodeID:
                return self.txn['sender']




class AccountCell:

        def __init__(self):
                self.H = HashDigest()

        def makeAccountCell(self, path, cell):
                #read cell data
                f = open(path, "r")
                text = f.read()
                f.close()
                #make ledger cell
                cell.initCell('account')
                strCData = json.loads(text)[1]
                strNData = json.loads(text)[0]
                cell.cData.setAccountStatement(strCData)
                self.makeNData(cell, strNData)
                #h = self.H.generate(text)
                #cell.nuc.nData.setContentHash(h)
                strChkCell = """

def checkCell(cellString):
    cell = Cell("")
    cell.parse(cellString)

    #check if cell data contains all valid transactions    
    transactions = cell.cData.getAccountStatement()     #FN
    transactions = json.loads(transactions)
    if not cell.nuc.nData.hasValidTxns(transactions):   #FN
        return False
    
    #check if account balance comes from Account Statement and RCTL
    accountBalance = cell.nuc.nData.getBalance()        #FN
    RCTL = cell.nuc.nData.getRecentlyClosed()           #FN
    selfID = cell.nuc.nData.getNodeID()                 #FN
    amount = 0
    for txn in transactions:
        T = Transaction()
        T.parse(txn)
        if T.getSender() == selfID:                     #
            amount = amount - T.getAmount()             #
        elif T.getReceiver() == selfID:                 #
            amount = amount + T.getAmount()
    RCTL = json.loads(RCTL)
    for txn in RCTL:
        T = Transaction()
        T.parse(txn)
        if T.getSender() == selfID:
            amount = amount - T.getAmount()
        elif T.getReceiver() == selfID:
            amount = amount + T.getAmount()
    if accountBalance != amount:
        return False
    return True

"""
                strChkNext = """

def checkNext(nucStr, nucNStr):
    nuc = Nucleus("")
    nuc.parse(nucStr)
    nucN = Nucleus("")
    nucN.parse(nucNStr)
    EF = ExecuteFetch()                                 #CL
    
    #valid nodeID?
    nodeID = EF.getNodeID(nuc)                          #CL:FN
    if nucN.nData.getNodeID not in nodeID:              #FN
        return False

    #valid brnchID?
    branchID = nucN.nData.getBranch()                   #FN
    if not EF.isBranch(branchID):                       #CL:FN
        return False

    #empty previous nucleus case
    if isinstance(nuc.nData, EmptyNData):
        if not nucN.nData.isInitNdata():                #FN
            return False

    #non-empty previous nucleus case
    elif isinstance(nuc.nData, AccountNData):
        #nuclear code checks
        if nuc.strChkCell != nucN.strChkCell or nuc.strChkNext != nucN.strChkNext or nuc.strChkPrev != nucN.strChkPrev:
            return False

        #same nodeID and branchID
        if nuc.nData.getNodeID() != nucN.nData.getNodeID() or nuc.nData.getBranch() != nucN.nData.getBranch():
            return False
        selfID = nuc.nData.getNodeID()
        branch = nuc.nData.getBranch()

        #check if nextNuc epoch = branch epoch
        branchEpoch = EF.getBranchEpoch(branch)         #CL:FN
        if branchEpoch != nucN.nData.getEpoch()         #FN
            return False

        #transaction validation OTL, RCTL
        currentOTL = nuc.nData.getOutstanding()
        currentRCTL = nuc.nData.getRecentlyClosed()
        currentOTL = json.loads(currentOTL)
        currentRCTL = json.loads(currentRCTL)
        if not nuc.nData.hasValidTransactions(currentOTL) or not nuc.nData.hasValidTransactions(currentRCTL):
            return False
        nextOTL = nucN.nData.getOutstanding()
        nextRCTL = nucN.nData.getRecentlyClosed()
        nextOTL = json.loads(nextOTL)
        nextRCTL = json.loads(nextRCTL)
        if not nucN.nData.hasValidTransactions(nextOTL) or not nucN.nData.hasValidTransactions(nextRCTL):
            return False

        #balance checks
        currentBalance = nuc.nData.getBalance()
        nextBalance = nucN.nData.getBalance()
        B = currentBalance
        for txn in nextRCTL:
            T = Transaction()
            T.parse(txn)
            pf = False
            for t in currentRCTL:
                if t == txn:
                    pf = True
            if pf == False:
                if T.getSender() == selfID:         #
                    B = B - T.getAmount()
                elif T.getReceiver() == selfID:     #
                    B = B + T.getAmount()
        if B != nextBalance:
            return False

        #transaction transitions check
        for txn in currentOTL:
            T = Transaction()
            T.parse(txn)
            pf = False
            for t in nextOTL:
                if t == txn:
                    pf = True
            for t in nextRCTL:
                if t == txn:
                    pf = True
                    if T.isInitiator():             #
                        if not EF.isOutstanding(T.getTxnID(), T.getResponder(selfID)):    #CL:FN
                            return False
                    elif T.isResponder():           #
                        if not EF.isRecentlyClosed(T.getTxnID(), T.getInitiator(selfID)): #CL:FN
                            return False
            if pf == False:
                return False

        for txn in nextOTL:
            T = Transaction()
            T.parse(txn)
            pf = False
            for t in currentOTL:
                if t == txn:
                    pf = True
            if pf == False:
                if T.isInitiator():
                    type = EF.getCellType(T.getResponder(selfID))         #CL:FN
                elif T.isResponder():
                    type = EF.getCellType(T.getInitiator(selfID))
                if type != 'branch' and type != 'account':
                    return False
                if T.isSender(selfID):
                    if T.getAmount() > nextBalance:
                        return False

        if nuc.nData.getEpoch() != nucN.nData.getEpoch():
            if nucN.nData.getEpoch() != 0 and nucN.nData.getEpoch() != nuc.nData.getEpoch()+1:
                return False
            if len(nextRCTL) != 0:
                return False
        else:
            for txn in currentRCTL:
                pf = False
                for t in nextRCTL:
                    if t == txn:
                        pf = True
                if pf == False:
                    return False

        for txn in nextRCTL:
            pf = False
            for t in currentRCTL:
                if t == txn:
                    pf = True
            for t in nextOTL:
                if t == txn:
                    pf = True
            if pf == False:
                return False

    #invalid nucleus case
    else:
        return False
    return True

"""
                strChkPrev = """

def checkPrevious( nucStr, nucPStr):
    nuc = Nucleus("")
    nuc.parse(nucPStr)
    nucN = Nucleus("")
    nucN.parse(nucStr)
    EF = ExecuteFetch()                                 #CL
    
    #valid nodeID?
    nodeID = EF.getNodeID(nuc)                          #CL:FN
    if nucN.nData.getNodeID not in nodeID:              #FN
        return False

    #valid brnchID?
    branchID = nucN.nData.getBranch()                   #FN
    if not EF.isBranch(branchID):                       #CL:FN
        return False

    #empty previous nucleus case
    if isinstance(nuc.nData, EmptyNData):
        if not nucN.nData.isInitNdata():                #FN
            return False

    #non-empty previous nucleus case
    elif isinstance(nuc.nData, AccountNData):
        #nuclear code checks
        if nuc.strChkCell != nucN.strChkCell or nuc.strChkNext != nucN.strChkNext or nuc.strChkPrev != nucN.strChkPrev:
            return False

        #same nodeID and branchID
        if nuc.nData.getNodeID() != nucN.nData.getNodeID() or nuc.nData.getBranch() != nucN.nData.getBranch():
            return False
        selfID = nuc.nData.getNodeID()
        branch = nuc.nData.getBranch()

        #check if nextNuc epoch = branch epoch
        branchEpoch = EF.getBranchEpoch(branch)         #CL:FN
        if branchEpoch != nucN.nData.getEpoch()         #FN
            return False

        #transaction validation OTL, RCTL
        currentOTL = nuc.nData.getOutstanding()
        currentRCTL = nuc.nData.getRecentlyClosed()
        currentOTL = json.loads(currentOTL)
        currentRCTL = json.loads(currentRCTL)
        if not nuc.nData.hasValidTransactions(currentOTL) or not nuc.nData.hasValidTransactions(currentRCTL):
            return False
        nextOTL = nucN.nData.getOutstanding()
        nextRCTL = nucN.nData.getRecentlyClosed()
        nextOTL = json.loads(nextOTL)
        nextRCTL = json.loads(nextRCTL)
        if not nucN.nData.hasValidTransactions(nextOTL) or not nucN.nData.hasValidTransactions(nextRCTL):
            return False

        #balance checks
        currentBalance = nuc.nData.getBalance()
        nextBalance = nucN.nData.getBalance()
        B = currentBalance
        for txn in nextRCTL:
            T = Transaction()
            T.parse(txn)
            pf = False
            for t in currentRCTL:
                if t == txn:
                    pf = True
            if pf == False:
                if T.getSender() == selfID:         #FN
                    B = B - T.getAmount()
                elif T.getReceiver() == selfID:     #FN
                    B = B + T.getAmount()
        if B != nextBalance:
            return False

        #transaction transitions check
        for txn in currentOTL:
            T = Transaction()
            T.parse(txn)
            pf = False
            for t in nextOTL:
                if t == txn:
                    pf = True
            for t in nextRCTL:
                if t == txn:
                    pf = True
                    if T.isInitiator():             #FN
                        if not EF.isOutstanding(T.getTxnID(), T.getResponder()):    #FN, CL:FN
                            return False
                    elif T.isResponder():           #FN
                        if not EF.isRecentlyClosed(T.getTxnID(), T.getInitiator()): #FN, CL:FN
                            return False
            if pf == False:
                return False

        for txn in nextOTL:
            T = Transaction()
            T.parse(txn)
            pf = False
            for t in currentOTL:
                if t == txn:
                    pf = True
            if pf == False:
                if T.isInitiator():
                    type = EF.getCellType(T.getResponder(selfID))         #CL:FN
                elif T.isResponder():
                    type = EF.getCellType(T.getInitiator(selfID))
                if type != 'branch' and type != 'account':
                    return False
                if T.isSender(selfID):
                    if T.getAmount() > nextBalance:
                        return False

        if nuc.nData.getEpoch() != nucN.nData.getEpoch():
            if nucN.nData.getEpoch() != 0 and nucN.nData.getEpoch() != nuc.nData.getEpoch()+1:
                return False
            if len(nextRCTL) != 0:
                return False
        else:
            for txn in currentRCTL:
                pf = False
                for t in nextRCTL:
                    if t == txn:
                        pf = True
                if pf == False:
                    return False

        for txn in nextRCTL:
            pf = False
            for t in currentRCTL:
                if t == txn:
                    pf = True
            for t in nextOTL:
                if t == txn:
                    pf = True
            if pf == False:
                return False

    #invalid nucleus case
    else:
        return False
    return True

"""
                cell.nuc.strChkCell = strChkCell
                cell.nuc.strChkNext = strChkNext
                cell.nuc.strChkPrev = strChkPrev
                return cell


        def makeNData(self, cell, strNData):
                blocks = cell.cData.getAccountStatement()
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

class AccountCData(CellData):
        Data = None

        def __init__(self, string: str):
                #self.parse(string)
                self.Data = {}
                self.Data['accountStatement'] = {}

        def toString(self):
            return json.dumps({'accountStatement': self.getAccountStatement()})

        def parse(self, stringData: str):
                data = json.loads(stringData)
                self.setAccountStatement(data['accountStatement'])
                #self.Data[' = json.loads(stringData)

        def getAccountStatement(self):
                txnList = []
                for txnID in self.Data['accountStatement']:
                    txnList.append(self.Data['accountStatement'][txnID].toString())
                return json.dumps(txnList)

        def setAccountStatement(self, data):
                if isinstance(data, str):
                        data = json.loads(data)
                self.Data['accountStatement'] = {}
                for txn in data:
                    T = Transaction()
                    T.parse(txn)
                    tID = T.getTxnId()
                    self.Data[tID] = Transaction()
                    self.Data[tID].parse(txn)


#------NUCLEAR DATA-----------


class AccountNData(NuclearData):
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








class BranchCell:

        def __init__(self):
                self.H = HashDigest()

        def makeBranchCell(self, path, cell):
                #read cell data
                f = open(path, "r")
                text = f.read()
                f.close()
                #make ledger cell
                cell.initCell('branch')
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

class BranchCData(CellData):
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


class BranchNData(NuclearData):
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
