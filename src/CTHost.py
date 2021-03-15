# coding: utf-8
import time
import threading
from multiprocessing import Pipe, Queue
import os
import json
import portalocker
from prompt_toolkit import prompt


from Config import Config, WrkrConfig
from Modules import Modules
from Communication import Communication
from Cell import Cell, Nucleus
from shell import Shell
from CT0CreateNode import HostCreateNode

hostCommands = ['switch-node', 'node-info', 'cell-info', 'select-cell', 'create-node', 'list-nodes', 'quit']

class Host:

    def __init__(self,workdir):
            
            print("Initializing host environment")
            self.con = Config(workdir)
            print('Starting wrkrs')
            self.wrkrSet = []
            self.wrkrPipes = {}
            self.comm = Communication(self.con)
            self.tC = threading.Thread(target=self.comm.listen, args=())
            self.tC.start() 
            self.createNode = HostCreateNode(self, self.comm)
            self.tCN = threading.Thread(target=self.createNode.joinCrewListener, args=())
            self.tCN.start()
            self.shellQueue = Queue()
            wrkrList = self.readWrkrs()
            for wrkr in wrkrList:
                self.startWrkr(wrkr)
            self.shell = Shell(self.con.fig['name'], hostCommands, self.shellQueue, self.wrkrPipes)

    def startWrkr(self, wrkr):
        t = threading.Thread(target=lambda w,c: Wrkr(w,c), args=(wrkr,self))
        t.start()
        self.wrkrSet.append(t)

    def readWrkrs(self):
        Clist = []
        f = open(self.con.fig['wrkrlistfile'], "r")
        text = f.read()
        f.close()
        text = text.split('\n')
        for Cid in text:
            if Cid != "":
                Clist.append(Cid)
        return Clist

    # call back function used by wrkrShell 
    def pipeWrkr(self, nodeID, commandPipe):
        self.wrkrPipes[nodeID] = commandPipe

    def writeWrkr(self, nodeID, configText=None):
        # make directory
        wrkdir = self.con.fig['wrkrsdir'] + nodeID + "/"
        configfile = wrkdir + "config.txt"
        os.system("mkdir -p " + wrkdir)
        os.system("touch " + configfile)
        if configText is not None:
            with open(configfile,"w") as f:
                f.write(configText)

class Wrkr:

    def __init__(self, nodeID, host: Host):
        self.con = WrkrConfig(host.con,nodeID)
        self.host = host
        self.host.comm.addCommQueue(self)
        self.modules = Modules(self)
        print(self.host.con.fig['name']+" : worker in crew "+self.con.nodeID)
        #cell = Cell(cellPath)
        #self.modules.store.updateCell(cell)
        self.wrkrShell()

    # TODO: Needs to be updated
    def wrkrShell(self):
        # open a pipe and call back host
        remote, local = Pipe()
        self.host.pipeWrkr(self.con.nodeID,remote)

        while True:
            try:
                command = local.recv()
                if command != "":
                    comargs = command.split()
                    #self.shellOut('Command received')
                    if comargs[0] == "node-info":
                        self.shellOut(self.con.print())
        
                    elif comargs[0] == "cell-info":
                        self.modules.store.currentCell.print()
        
                    elif comargs[0] == "create-node":        
                        #self.shellOut("not implemented yet")
                        if len(comargs) < 2:
                            self.shellOut("missing parameters")
                        else:
                            childID = comargs[1]
                            path = "../run/aux/hashes"
                            try:
                                path = comargs[2]
                            except:
                                pass
                            flag = self.modules.createNode.newNode(childID, path, 'init')
                            self.shellOut("create Node : "+str(flag))

                    elif comargs[0] == "select-cell":
                        #self.shellOut("not implemented yet")
                        if len(comargs) < 2:
                            self.shellOut("missing parameters")
                        else:
                            Ctype = comargs[1]
                            path = "../run/aux/newCData.txt"
                            try:
                                path = comargs[2]
                            except:
                                pass
                            self.modules.selectCell.getData(Ctype, path)

                    #elif comargs[0] == "store-clean":     
                    #    self.shellOut("not implemented yet")
                    else:
                        self.shellOut('Unknown command')
            except Exception as ex:
                self.shellOut("ERROR: " + str(ex))

    def shellOut (self, msg):
        msg = [ self.con.nodeID, msg ]
        self.host.shellQueue.put(msg)

