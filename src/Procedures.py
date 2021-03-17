from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import dsa
import json

from Config import Config, WrkrConfig
from Cell import Cell, Nucleus
from CT0Execute import Execute
#from CT0Leafward import Leafward
#from CT0Rootward import Rootward
from CT0Fetch import Fetch
from CT0Discover import Discover
from CT0Store import POA, MNode, UUList, AssimData




"""
TODO: There should be 2 versions of the Procedures class:
Procedures and ClntProcedures (for use in hosts and clients, resp.).
ClntProcedures will have the read (and verify).
It doesn't have a crew associated with it.
"""


class Procedures:

        @staticmethod
        def evolve(wrkr,newCell):        #cell object
                cell = wrkr.modules.store.currentCell #cell object
                
                strCode = newCell.nuc.strChkCell
                ArgsArray = []
                ArgsArray.append(newCell.toString())
                flag1 = wrkr.modules.execute.exe("chkCell", strCode, ArgsArray)
                
                strCode = newCell.nuc.strChkPrev
                ArgsArray = []
                ArgsArray.append(newCell.nuc.toString())
                ArgsArray.append(cell.nuc.toString())
                flag2 = wrkr.modules.execute.exe("chkPrev", strCode, ArgsArray)
                
                strCode = cell.nuc.strChkNext
                ArgsArray = []
                ArgsArray.append(cell.nuc.toString())
                ArgsArray.append(newCell.nuc.toString())
                flag3 = wrkr.modules.execute.exe("chkNext", strCode, ArgsArray)
                
                print("EVOLVE : ",[flag1,flag2,flag3])
                
                if flag3 and flag2 and flag1:
                        wrkr.modules.store.uuList.add(newCell.nuc)
                        print("length of UUList : ", len(wrkr.modules.store.uuList.uuList))
                        wrkr.modules.store.updateCell(newCell)
                        return True
                else:
                        return False

                #uses STORE.UULIST, STORE.UPDATECELL, EXECUTE


        
        @staticmethod
        def leafward(wrkr):
                #rootID, crewrootID, poa[rootID, nodeID] <-- leafward.receive
                print("Doing LEAFWARD\n\n\nLEAFWARD ", wrkr.con.nodeID)
                AssimilatedInfo = wrkr.modules.leafward.receive()
                rootID = AssimilatedInfo[0]
                crewRoot = AssimilatedInfo[1]
                Ipoa = AssimilatedInfo[2]
                #mtree, sign <-- poa[rootID, nodeID]     mTree = POA.merklePath    sign = POA.sign
                # h <-- hash.meval(mtree)
                #crewsign.verify(rootCrew, h, sign) == true
                if Ipoa.checkPOA() == True:
                        #store.addpoa(poa, h)
                        #cell = wrkr.getCell() # TODO: Add method
                        wrkr.modules.store.poaStore.addPOA("root", Ipoa)
                        #L <-- leafward.pickleaves(rootID)
                        leaves = wrkr.modules.leafward.pickLeaves(rootID)
                        #mtree[nodeID, L] <-- store.getmtree(L, nodeID, h)
                        poa = POA(None, None, wrkr.con)
                        poa.parse(Ipoa.toString())
                        
                        mTree = wrkr.modules.store.mmTree.getTree(leaves, wrkr.con.nodeID, poa)
                        if mTree != None:
                            if not wrkr.con.isRoot():
                                #mtree[rootID, L] <-- store.mmtree.concat(mtree[rootID, nodeID], mtree[nodeID, L])
                                mTree = wrkr.modules.store.mmTree.concat(poa.merklePath, mTree)
                        #poaset[rootID, L] <-- mtree[rootID, L], sign
                            #print("MTree after Concat : ", mTree)
                            poaSet = {}
                            signature = Ipoa.sign
                            path = Ipoa.merklePath
                            #print("poa sign : ", poa.sign)
                            #Ipoa.printPOApath()
                            mPath = {}
                            for l in leaves:
                                lastMNode = {}
                                lhash = ""
                                for n in mTree:
                                    if l == mTree[n].nodeID:
                                        lastMNode[n] = mTree[n]
                                        lhash = n
                                mPath[l] = {}
                                for n in path:
                                    mPath[l][n] = path[n]
                                try:
                                    mPath[l][lhash] = lastMNode[lhash]
                                    poaSet[l] = POA(mPath[l], signature, wrkr.con)
                                
                                    if not poaSet[l].checkPOA():
                                        del poaSet[l]
                                except:
                                    pass
                            #print(poaSet)
                            #for P in poaSet:
                            #    poaSet[P].printPOApath()
                            wrkr.modules.leafward.send(poaSet)
                        print(wrkr.con.nodeID, "LEAFWARD DONE!")
                #uses LEAFWARD(RECEIVE, PICKLEAVES, SEND), HASHDIGEST.MEVAL, CREWSIGN.VERIFY, STORE(ADDPOA, GETMTREE, CONCAT)
                
                
        @staticmethod
        def rootward(wrkr):
                leaves = wrkr.modules.rootward.monitored()
                mT = [None, None]
                h = [None, None]
                for b in [0,1]:
                        if not wrkr.con.isRoot():
                                mT[b] = Procedures.acceptVerify(wrkr,wrkr.con.nodeID+str(b), leaves)
                        else:
                                mT[b] = Procedures.acceptVerify(wrkr,str(b), leaves)
                        if mT[b] != None:
                                h[b] = wrkr.con.hasher.mEval(mT[b])
                #print("AcceptVerify results :: ", mT[0], mT[1])
                uuList = wrkr.modules.store.uuList.flush()
                #print("UUList : ", uuList)
                cell = wrkr.modules.store.currentCell
                #print("cell :  ", cell)
                nonce = wrkr.modules.rootward.getNonce()#.hasher.generateNonce()
                #print("NONCE : ", wrkr.con.nodeID, nonce)
                node = None
                mTree = {}
                if cell != None:
                        node = MNode(wrkr.con.nodeID, cell.nuc, nonce, h[0], h[1])
                        cuHash = wrkr.con.hasher.getCumulativeHash(node)
                        mTree[cuHash] = node
                        for b in [0,1]:
                                if mT[b] is not None:
                                        for n in mT[b].keys():
                                                mTree[n] = mT[b][n]
                        #print("mekle tree : ", mTree)
                        if wrkr.con.isRoot():
                                print("in root LW case")
                                #print("node: ", node.toString())
                                sign = wrkr.modules.crewSign.sign(node.toString(), "init")
                                #print("RW LW cuHash sign: ", sign)
                                #print("hashes :", h[0], h[1])
                                poaSet = {}
                                for b in [0,1]:
                                    mPath = {}
                                    if h[b] != None:
                                        mPath[cuHash] = node
                                        mPath[h[b]] = mTree[h[b]]
                                        poa = POA(mPath, sign, wrkr.con)
                                        poaSet[str(b)] = poa
                                poa = POA({cuHash: node}, sign, wrkr.con)
                                #print("setting poa", poa)
                                #poa.printPOApath()
                                #print("LEAFWARD poas : ", poaSet)
                                #for P in poaSet:
                                #    poaSet[P].printPOApath()
                                wrkr.modules.leafward.send(poaSet)
                                #print("back from leafward.send")
                                wrkr.modules.store.poaStore.add(cell, "root", poa)
                        print("assimilated :", cell)
                wrkr.modules.rootward.send(uuList, node)
                list = []
                for n in mTree:
                        list.append(mTree[n])
                wrkr.modules.store.mmTree.updateMMTree(list)
                if not wrkr.con.isRoot():
                    wrkr.modules.store.poaStore.addCell(cell)


        @staticmethod
        def acceptVerify(wrkr, nodeID, leaves):        #leaves: leaf node ids of monitored subtree
                inSubtree = False
                #print("AV params : ", nodeID, "   :::   ", leaves)
                if nodeID == 'root':
                        inSubtree = True
                else:
                        for l in leaves:
                                if l.startswith(nodeID):
                                        inSubtree = True
                #print("AV:",inSubtree)
                if not inSubtree:
                        return None
                #uulist, mnode <-- rootward.receive(nodeID)
                assimData = wrkr.modules.rootward.receive(nodeID)
                #print("AcceptVerify :: RW.rec -- ", assimData)
                uuList = None
                mNode = None
                sign = None
                if assimData != None:
                        uuList = assimData[1]
                        mNode = assimData[0]
                        sign = assimData[2]
                        #print(nodeID, " UUList : ", uuList.uuList)
                #lastMtree[nodeID, leaves] <-- store.getmtree(leaves, nodeID)                #latest version
                lastMtree = wrkr.modules.store.mmTree.getTree(leaves, nodeID, None)
                #print(lastMtree)
                AD = AssimData(wrkr.con)
                if not AD.verifyAssimData(sign, uuList, mNode, nodeID):
                    return lastMtree
                #nuc, nonce, h0, h1 <-- mnode
                #nucF <-- lastMtree.mNode.nuc
                if lastMtree != None:
                        
                        cuHash = wrkr.con.hasher.mEval(lastMtree)
                        nucF = lastMtree[cuHash].nuc
                        #newUUlist <-- [nucF, uulist]
                        newUUlist = UUList()
                        newUUlist.add(nucF)
                        if uuList != None:
                                #print("in non-empty uulist case")
                                for n in uuList.uuList:
                                        newUUlist.add(n)
                                if not Procedures.consistent(wrkr,newUUlist):
                                        return lastMtree    #reject update
                        else:
                                return lastMtree
                else:
                        if uuList != None:
                            #print("last mTree = None, non-empty uuList")
                            newUUlist = UUList()
                            newUUlist.add(Nucleus(''))
                            for n in uuList.uuList:
                                newUUlist.add(n)
                            if not Procedures.consistent(wrkr, newUUlist):
                                return lastMtree
                if mNode == None:
                        return lastMtree

                mTree0 = Procedures.acceptVerify(wrkr, nodeID+'0', leaves)
                if mTree0 != None:
                        if wrkr.con.hasher.mEval(mTree0) != mNode.lChildCuHash:
                                return lastMtree
                mTree1 = Procedures.acceptVerify(wrkr, nodeID+'1', leaves)
                if mTree1 != None:
                        if wrkr.con.hasher.mEval(mTree1) != mNode.rChildCuHash:
                                return lastMtree
                
                #return [mnode, mTree[nodeID0, leaves], mTree[nodeID1, leaves]]
                cuHash = wrkr.con.hasher.getCumulativeHash(mNode)
                #if mNode == None:
                #    return lastMtree
                mTree = {}
                mTree[cuHash] = mNode
                if mTree0 != None:
                    for n in mTree0.keys():
                        mTree[n] = mTree0[n]
                if mTree1 != None:
                    for n in mTree1.keys():
                        mTree[n] = mTree1[n]
                return mTree


                
        @staticmethod
        def consistent(wrkr, uulist):        #array of nuc
                uulist = uulist.uuList
                for i in range(len(uulist)-1):
                        
                        strCode = uulist[i+1].strChkPrev
                        ArgsArray = []
                        ArgsArray.append(uulist[i+1].toString())
                        ArgsArray.append(uulist[i].toString())
                        flag1 = wrkr.modules.execute.exe("chkPrev", strCode, ArgsArray)
                        
                        strCode = uulist[i].strChkNext
                        ArgsArray = []
                        ArgsArray.append(uulist[i].toString())
                        ArgsArray.append(uulist[i+1].toString())
                        flag2 = wrkr.modules.execute.exe("chkNext", strCode, ArgsArray)
                        
                        print("consistent : ", flag1, flag2)
                        if flag1 == False or flag2 == False:
                                return False
                return True


class ClntProcedures:

        @staticmethod
        def read(clnt, nodeID, rootID):        #private
                #print("in read procedure")
                crews = clnt.modules.discover.discoverFetch(nodeID, rootID)
                Ncrew = crews[0]        #node crew dictionary address:pubkey
                Rcrew = crews[1]        #root crew
                #print("node crew:  ", Ncrew)
                #print("root crew:  ", Rcrew)
                cellPoa = clnt.modules.fetch.getCell(nodeID, rootID)
                #print("Got Cell (not verified):", cell)
                if cellPoa != "no cell or poa":
                    if type(cellPoa) == str:
                        #print(cell)
                        #return None
                        CP = json.loads(cellPoa)
                        c = Cell('')
                        c.parse(CP[0])
                        p = POA(None,None,clnt.con)
                        p.parse(CP[1])
                    else:
                        c = cellPoa[0]        #cell
                        p = cellPoa[1]        #POA
                    if ClntProcedures.verify(clnt, nodeID, rootID, Rcrew, c, p):
                        print('verification succeeded')
                        return c
                    else:
                        print('verification failed')
                        return None
                else:
                    print(cellPoa)
                    return None


        
        @staticmethod
        def verify(clnt, nodeID, rootID, rootCrew, cell, poa):        #freshness check?
                #mtree, sign <-- poa[rootID, nodeID]  mTree = POA.merklePath  sign = POA.sign
                # h <-- hash.meval(mtree)
                #crewsign.verify(rootCrew, h, sign) == true
                #print('0: In read verification')
                if poa.checkPOA() == True:
                        #mtree.terminals == nodeID and mtree.root == rootID
                        #print("1: check POA true")
                        root = poa.merklePath[clnt.con.hasher.mEval(poa.merklePath)].nodeID
                        #print(root)
                        terminal = ""
                        terminalH = ""
                        for h in poa.merklePath:
                                flag = False
                                for n in poa.merklePath:
                                        if poa.merklePath[h].lChildCuHash == n or poa.merklePath[h].rChildCuHash == n:
                                                flag = True
                                if flag == False:
                                        terminal = poa.merklePath[h].nodeID
                                        terminalH = h
                                        break
                        #print("terminal, nodeID : ", terminal, nodeID)
                        #print(terminalH)
                        if terminal == nodeID and root == rootID:
                                #print("2: terminal and root match")
                                #cell.nuc == mtree.mnode.nuc
                                if cell.nuc.toString() == poa.merklePath[terminalH].nuc.toString():
                                        #print("3: cell and poa match")
                                        #chkCell(cell) == true
                                        strCode = cell.nuc.strChkCell
                                        ArgsArray = []
                                        ArgsArray.append(cell.toString())
                                        flag1 = clnt.modules.execute.exe("chkCell", strCode, ArgsArray)
                                        #print("4: check cell ", flag1)
                                        if flag1 == True:
                                                return True
                return False

                
        #uses DISCOVER, FETCH.GETCELL, HASHDIGEST.MEVAL, CREWSIGN.VERIFY, EXECUTE
