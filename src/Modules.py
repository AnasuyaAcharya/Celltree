import os
import time
import threading

from Config import Config, WrkrConfig
from Procedures import Procedures, ClntProcedures
from Cell import Cell, Nucleus
from HashDigest import HashDigest
from Communication import Communication, ClntCommunication
from CrewSign import CrewSign, ClntSign

from CT0ModuleManager import ModuleManager
from CT0Execute import Execute
from CT0Store import Store
from CT0Fetch import Fetch, ClntFetch
from CT0Discover import Discover, ClntDiscover
from CT0SelectCell import SelectCell
from CT0CreateNode import CreateNode
from CT0Leafward import Leafward
from CT0Rootward import Rootward


class Modules:

    def __init__(self, wrkr):
        self.wrkr = wrkr
        self.wrkrcon = wrkr.con
        self.modulethreads = []
        self.moduleManager = ModuleManager()
        self.thrd(self.moduleManager.listener)

        self.createNode = CreateNode(wrkr, self.wrkr.host.comm)       #PROBLEM: needs Wrkr, not wrkrcon
        self.thrd(self.createNode.listener)

        self.store = Store(self.wrkrcon)
        self.thrd(self.store.listener) #STORE GC

        self.crewSign = CrewSign(self.wrkrcon, self.wrkr.host.comm)
        self.thrd(self.crewSign.listener)

        self.fetch = Fetch(self.wrkr, self.store)     
        self.thrd(self.fetch.listener)  #FETCH

        self.discover = Discover(self.wrkrcon, self.fetch)

        self.execute = Execute()

        #self.thrd(self.createNode.crewListener)    #CREATE NODE

        self.selectCell = SelectCell(self.wrkr, self.wrkr.host.comm)         #review!!!
        self.thrd(self.selectCell.listener)
            
        self.leafward = Leafward(self.wrkr)        #review!!!
        self.thrd(self.leafward.scheduler)
        self.thrd(self.leafward.listener)
            
        self.rootward = Rootward(self.wrkr)        #review!!!
        self.thrd(self.rootward.scheduler)
        self.thrd(self.rootward.listener)
                        
    def thrd(self,target,args=()):
        t = threading.Thread(target=target,args=args)
        t.start()
        self.modulethreads.append(t)


class ClntModules:
    def __init__(self, clnt):
        self.con = clnt.con
        self.modulethreads = []
        
        self.communication = clnt.comm
        #self.thrd(self.communication.listen)
        
        #self.moduleManager = ModuleManager()
        #self.thrd(self.moduleManager.listener)
        
        self.execute = Execute()
        self.clntSign = ClntSign(self.con)

        self.fetch = ClntFetch(self.con, self.communication)
        self.discover = ClntDiscover(self.con, self.fetch)

    def thrd(self,target,args=()):
        t = threading.Thread(target=target,args=args)
        t.start()
        self.modulethreads.append(t)

#-------------------------------------------

