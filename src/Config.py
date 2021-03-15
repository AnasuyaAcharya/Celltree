from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives import serialization 
import os
import json

from HashDigest import HashDigest

# A general utility class
class CrewInfo:

    @staticmethod
    def read(filename):        
        text = ""
        with open(filename, "r") as f:
            text = f.read()
        return CrewInfo.parse(text)

    @staticmethod
    def write(filename, text: str):
        with open(filename, "w") as f:
            f.write(text)

    @staticmethod
    def parse(text: str):
        members = []
        if len(text) == 0:
            return members
        members = json.loads(text) #list of members
        return members
        
    @staticmethod
    def toString(CrewMembers, nodeID=None): 
        strCrew = json.dumps(CrewMembers)
        if nodeID is None:
            return strCrew
        else:
            return json.dumps([str(nodeID), strCrew])

class Config:

    def __init__(self, hostdir: str):
        # if client credentials exist in file, read and initialize
        # else create new client credentials and write to file, initialize
        hostdir = hostdir + ("" if hostdir[-1] == "/" else "/")
        #print('Host starting up at', hostdir)
        self.configfile = hostdir + "config.txt"
        with open(self.configfile) as f:
            c = f.read()
            self.fig = json.loads(c)

        self.fig['wrkrsdir'] = hostdir + "wrk/"   # working space for each wrkr
        self.fig['crewsdir'] = hostdir + "crews/"   # discovered crews 
        self.fig['vardir'] = hostdir + "var/"
        self.fig['wrkrlistfile'] = self.fig['wrkrsdir'] + "wrkrList.txt"
        self.fig['dfltwrkrconfile'] = hostdir + "wrkrconfig.txt"
        self.fig['logfile'] = self.fig['vardir'] + "log.txt"
        self.fig['keydir'] = hostdir + "key/"
        self.fig['keyfile'] = self.fig['keydir'] + "host.pem"
        self.fig['myaddrfile'] = self.fig['keydir'] + "addr.txt"
        addrdir = hostdir + self.fig['addrdir']  # recommnded value: "../addr/"
        addrdir = addrdir + ("" if addrdir[-1] == "/" else "/")
        self.fig['addressbook'] = addrdir + "addr.txt"
        self.fig['rootcrewfile'] = addrdir + "rootCrew.txt"
        self.mkfiles()
        self.wrkrs = []
        H = HashDigest()
        try:
            #read host private key
            f = open(self.fig['keyfile'], "rb")
            pvtkey = f.read()
            f.close()
            self.fig['pvtkey'] = serialization.load_pem_private_key( pvtkey , password=b'password' , backend=default_backend() )
            self.fig['pubkey'] = self.fig['pvtkey'].public_key()
            pkenc = self.fig['pubkey'].public_bytes(encoding = serialization.Encoding.PEM, format = serialization.PublicFormat.SubjectPublicKeyInfo)
            self.fig['addr'] = H.generate(str(pkenc))
        except FileNotFoundError:
            #--CREATE A NEW HOST--  
            proceed = input('No key found. Create a new host? [y/N] ')
            if proceed != 'y':
                print('Exiting')
                os._exit(1)
            #make new private key
            self.fig['pvtkey'] = dsa.generate_private_key( key_size=1024, backend=default_backend() )
            self.fig['pubkey'] = self.fig['pvtkey'].public_key()
            pkenc = self.fig['pubkey'].public_bytes(encoding = serialization.Encoding.PEM, format = serialization.PublicFormat.SubjectPublicKeyInfo)
            self.fig['addr'] = H.generate(str(pkenc))

            pem = self.fig['pvtkey'].private_bytes( encoding=serialization.Encoding.PEM , format=serialization.PrivateFormat.PKCS8 , encryption_algorithm=serialization.BestAvailableEncryption(b'password') )
            with open(self.fig['keyfile'], "wb") as f:
                f.write(pem)
            #make file structure
            #add self to addressbook
            myaddr = { self.fig['addr'] : [ self.fig['IP'], self.fig['port'], pkenc.decode("utf-8") ] }
            #self.saveAddress(self.fig['addressbook'], myaddr)
            with open(self.fig['myaddrfile'], "w") as f:
                json.dump(myaddr,f)

            with open(self.fig['keydir']+"pubkey.txt", "w") as f:
                json.dump([pkenc.decode("utf-8")], f)

            print("Initialized host address. Restart after setting up any wrkrs.")
            os._exit(0)

    def mkfiles(self):
        os.system("mkdir -p " + self.fig['keydir'])
        os.system("mkdir -p " + self.fig['vardir'])
        os.system("mkdir -p " + self.fig['wrkrsdir'])
        os.system("mkdir -p " + self.fig['crewsdir'])
        os.system("touch " + self.fig['logfile'])
        os.system("touch " + self.fig['wrkrlistfile'])
        os.system("touch " + self.fig['dfltwrkrconfile'])

    def saveAddress(self, path, addr, overwrite=False):
        if overwrite:
            with open(path, "w") as f:
                json.dump(addr,f)
        else:
            with open(path, "r+") as f:
                #portalocker.lock(f, portalocker.LOCK_EX)
                book = json.load(f)
                book.update(addr)
                f.seek(0)
                f.truncate()
                json.dump(book,f)
    
    def getCrewInfo(self, nodeID):
        path = ""
        if nodeID == 'root':
            path = self.fig['rootcrewfile']
        elif nodeID in self.wrkrs: # among local workers
            path = self.fig['wrkrsdir']+nodeID+"/members.txt"
        else:
            path = self.fig['crewsdir']+nodeID#+".txt"
        try:
            return CrewInfo.read(path)
        except IOError:
            return None        

class WrkrConfig:
    def __init__(self, hostcon: Config, nodeID: str):
        # nodeID is a binary string, or "root", or "mngr"
        self.nodeID = nodeID
        self.hostcon = hostcon
        self.wrkdir = hostcon.fig['wrkrsdir'] + nodeID + "/"
        # read parameters from default config file, and then update with local config
        try:
            with open(hostcon.fig['dfltwrkrconfile']) as f:
                c = f.read()
                self.fig = json.loads(c)
        except:
            print("Fatal Error: could not read default wrkr configuration")
            os._exit(1)
        try:
            with open(self.wrkdir+"config.txt") as f:
                c = f.read()
                localconfig = json.loads(c)
                self.fig.update(localconfig)
        except FileNotFoundError:
            pass
            #print("Using default wrkr configuration.")
        self.mkfiles()
        self.members = CrewInfo.read(self.fig['files']['members'])
        self.hasher = HashDigest()
        self.hostcon.wrkrs.append(nodeID)

    def mkfiles(self):
        # check if all files have been configured
        if self.fig.get('files') is None:
            self.fig['files'] = {}
        os.system("mkdir -p " + self.wrkdir)
        self.fig['files'].setdefault('members','members.txt')
        self.fig['files'].setdefault('cell','cell.txt')
        self.fig['files'].setdefault('assimData','assimData.txt')
        self.fig['files'].setdefault('poaStore','poa.txt')
        self.fig['files'].setdefault('mmtree','mmtree.txt')
        for f in self.fig['files']:
            self.fig['files'][f] = self.wrkdir + self.fig['files'][f]
            os.system("touch " + self.fig['files'][f])

    def print(self):
        #strWrkrFig = json.dumps(self.fig)
        #strHostFig = json.dumps(self.hostcon.fig)
        strNodeID = 'Node ID : '+self.nodeID
        print(strNodeID , '\n' , 'Members : ' , self.members , '\n' , self.fig , '\n' , self.hostcon.fig)
        #return strConfig

    def isRoot(self):
        return self.nodeID == 'root'

    def getCrewInfo(self, nodeID):
        path = ""
        if nodeID == "":
            return self.members
        elif nodeID == 'root':
            path = self.hostcon.fig['rootcrewfile']
        elif nodeID in self.hostcon.wrkrs: # among local workers
            path = self.hostcon.fig['wrkrsdir']+nodeID+"/members.txt"
        else:
            path = self.hostcon.fig['crewsdir']+nodeID#+".txt"
        try:
            return CrewInfo.read(path)
        except IOError:
            return None        


class ClntConfig:

    def __init__(self, topdir: str):
        # if client credentials exist in file, read and initialize
        # else create new client credentials and write to file, initialize
        clidir = topdir + ("" if topdir[-1] == "/" else "/")
        #print('Client starting up at', clidir)
        self.configfile = clidir + "config.txt"
        with open(self.configfile) as f:
            c = f.read()
            self.fig = json.loads(c)

        self.fig['crewsdir'] = clidir + "crews/"   # discovered crews 
        self.fig['vardir'] = clidir + "var/"
        self.fig['logfile'] = self.fig['vardir'] + "log.txt"
        #self.fig['keydir'] = clidir + "key/"
        #self.fig['keyfile'] = self.fig['keydir'] + "cli.pem"
        addrdir = clidir + self.fig['addrdir']  # recommnded value: "../addr/"
        addrdir = addrdir + ("" if addrdir[-1] == "/" else "/")
        self.fig['addressbook'] = addrdir + "addr.txt"
        self.fig['rootcrewfile'] = addrdir + "rootCrew.txt"
        self.mkfiles()
        H = HashDigest()
        self.hasher = HashDigest()

    def mkfiles(self):
        #os.system("mkdir -p " + self.fig['keydir'])
        os.system("mkdir -p " + self.fig['vardir'])
        os.system("mkdir -p " + self.fig['crewsdir'])
        os.system("touch " + self.fig['logfile'])

    def saveAddress(self, addr):
        with open(self.fig['addressbook'], "r+") as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            book = f.read()
            book = json.loads(book)
            book.update(addr)
            book = json.dumps(book)
            f.seek(0)
            f.truncate()
            f.write(book)

    def getCrewInfo(self, nodeID):
        path = ""
        if nodeID == 'root':
            path = self.fig['rootcrewfile']
        else:
            path = self.fig['crewsdir']+nodeID#+".txt"
        try:
            return CrewInfo.read(path)
        except IOError:
            #print("can't read path :: ", path)
            return None
        
#-------------------------------------------------
