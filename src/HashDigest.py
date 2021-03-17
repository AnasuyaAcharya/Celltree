from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
import os


class HashDigest:

        #for merkle hashes -- takes string, returns bytes
        def generate(self, message):
                #SHA256
                digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
                digest.update(str.encode(message))
                h = digest.finalize()
                return h.hex()

        def generateNonce(self):
                return os.urandom(16).hex()

        def mEval(self, mTree): #mTree dictionary        xx list of MNode (w/o cuHash)
                cuHashList = []
                for node in mTree:
                        cuHash = self.getCumulativeHash(mTree[node])
                        cuHashList.append(cuHash)
                ctr = 0
                ansHash = ""
                for h in cuHashList:
                        flag = False
                        for node in mTree:
                                if mTree[node].lChildCuHash == h:
                                        ctr = ctr + 1
                                        flag = True
                                elif mTree[node].rChildCuHash == h:
                                        ctr = ctr + 1
                                        flag = True
                        if flag == False:
                                ansHash = h
                if len(cuHashList) - ctr == 1:
                        return ansHash
                else:
                        return "invalid"

        def getCumulativeHash(self, node):    #MNode
                cuHash = None
                #print(node)
                if node != None:
                    internalHash = self.generate(node.nuc.toString() + node.nonce)
                    childHashes = ""
                    if node.lChildCuHash != None:
                        childHashes = childHashes + " 0: " + node.lChildCuHash
                    else:
                        childHashes = childHashes + " 0: None"
                    if node.rChildCuHash != None:
                        childHashes = childHashes + " 1: " + node.rChildCuHash
                    else:
                        childHashes = childHashes + " 1: None"
                    cuHash = self.generate(internalHash + childHashes)
                return cuHash







#-------------------------------------------------
"""H = HashDigest()
hash = H.generate("message")
#print(hash)
#print(H.generateNonce())


#make dummy tree nodes - one tree ROOT, 0, 1, 00, 01, 10, 11, xxx
from StaticCell import Cell, Nucleus
#from CT0Store import MNode
import json

class MNode:
        crewID = None
        nuc = None
        nonce = None
        rChildCuHash = ""
        lChildCuHash = ""

        def __init__(self, crewID, nuc, nonce, lPtr, rPtr):      #Nucleus, nonce, hash, hash
                self.crewID = crewID
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
                strNode['crewID'] = self.crewID
                strNode['nuc'] = self.nuc.toString()
                strNode['nonce'] = self.nonce
                strNode['lChildCuHash'] = self.lChildCuHash
                strNode['rChildCuHash'] = self.rChildCuHash
                strNode = json.dumps(strNode)
                return strNode

        def parse(self, strNode):
                strNode = json.loads(strNode)
                self.crewID = strNode['crewID']
                self.nuc = Nucleus("")
                self.nuc.parse(strNode['nuc'])
                self.nonce = strNode['nonce']
                self.lChildCuHash = strNode['lChildCuHash']
                self.rChildCuHash = strNode['rChildCuHash']


path = "Cells/1.txt"
cell = Cell(path)

node1 = MNode('1', cell.nuc, H.generateNonce(), '', '')
node10 = MNode('10', cell.nuc, H.generateNonce(), '', '')
node11 = MNode('11', cell.nuc, H.generateNonce(), '', '')
node100 = MNode('100', cell.nuc, H.generateNonce(), '', '')
node101 = MNode('101', cell.nuc, H.generateNonce(), '', '')
node110 = MNode('110', cell.nuc, H.generateNonce(), '', '')
node111 = MNode('111', cell.nuc, H.generateNonce(), '', '')

hash111 = H.getCumulativeHash(node111)
hash110 = H.getCumulativeHash(node110)
hash101 = H.getCumulativeHash(node101)
hash100 = H.getCumulativeHash(node100)
node11.updateL(hash110)
node11.updateR(hash111)
node10.updateL(hash100)
node10.updateR(hash101)
hash11 = H.getCumulativeHash(node11)
hash10 = H.getCumulativeHash(node10)
node1.updateL(hash10)
node1.updateR(hash11)
hash1 = H.getCumulativeHash(node1)

nlist = [node1, node10, node11, node100, node101, node110, node111]
nDict = {}
nDict[hash1] = node1
nDict[hash10] = node10
nDict[hash11] = node11
nDict[hash100] = node100
nDict[hash101] = node101
nDict[hash110] = node110
nDict[hash111] = node111


ans = H.mEval(nlist)
print(ans)
print(nDict[ans].toString())"""



