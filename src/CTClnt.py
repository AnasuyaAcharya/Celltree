# coding: utf-8
import time
import threading
import os
import json
import portalocker
from shell import Shell
from multiprocessing import Pipe, Queue

from Config import CrewInfo, ClntConfig
from Modules import ClntModules
from Communication import ClntCommunication
from Procedures import ClntProcedures
from Cell import Cell, Nucleus
from HashDigest import HashDigest


clntCommands = ['read-cell', 'discover-crew', 'show-crews', 'forget-crews', 'quit']

class Clnt:

    def __init__(self,workdir):
        print("Initializing client environment")
        self.con = ClntConfig(workdir)
        print('Modules starting')
        self.comm = ClntCommunication(self.con)
        self.modules = ClntModules(self)
        self.shellQueue = Queue()
        remote, local = Pipe()
        threading.Thread(target=self.handler, args=(local,)).start()
        self.shellPipe = { 'clnt' : remote }
        self.shell = Shell('client', clntCommands, self.shellQueue, self.shellPipe, 'clnt')

    def handler(self, pipe):
        while True:
            command = pipe.recv()
            if command != "":
                comargs = command.split()
                try:
                    if comargs[0] ==  "discover-crew":
                        #call to FETCH module
                        if len(comargs) != 2:
                            self.shellOut("Missing parameter")
                            continue
                        nodeID = comargs[1]
                        self.shellOut("discovering crew for " + nodeID)
                        crew = self.modules.discover.discover(nodeID)
                        self.shellOut(crew)
                        #print(self.modules.discover.getCrew(nodeID))
                        ##---------------
                    elif comargs[0] == "read-cell":        
                        #call to READ procedure
                        if len(comargs) != 2:
                            self.shellOut("Missing parameter")
                            continue
                        nodeID = comargs[1]
                        rootID = "root"
                        self.shellOut("reading cell from node " + nodeID + " with " + rootID + " as trust-root")
                        cell = ClntProcedures.read(self,nodeID,rootID)
                        if isinstance(cell, Cell):
                            cell.print()
                        else:
                            self.shellOut(cell)
                        #print(self.modules.procedures.read(nodeID, 'root'))
                    elif comargs[0] == "show-crews":        
                        #self.shellOut("not implemented yet")
                        path = self.con.fig['crewsdir']
                        for filename in os.listdir(path):
                            print(filename)

                    elif comargs[0] == "forget-crews":        
                        #self.shellOut("not implemented yet")
                        try:
                            crewID = comargs[1]
                            os.remove(self.con.fig["crewsdir"]+crewID)
                            self.shellOut(crewID+" removed.")
                        except:
                            self.shellOut("forgetting all crews")
                            path = self.con.fig['crewsdir']
                            for filename in os.listdir(path):
                                os.remove(path+filename)

                    else:
                        self.shellOut('Unrecognized command: ' + command)
                except Exception as e:
                    self.shellOut('ERROR: ' + str(e))
                    raise e
            

    def shellOut (self, msg):
        msg = [ 'client', msg ]
        self.shellQueue.put(msg)


