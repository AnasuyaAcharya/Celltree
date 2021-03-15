from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives import serialization 
import os
import json

from HashDigest import HashDigest
from Config import WrkrConfig
from CT0Discover import Discover
#Communication as arg, None for verify mode
#No Discover
#sign[address] = [pubkeyString, signHex]

class CrewSign:
        nodeID = None
        crewInfo = None #dictionary address:pub key

        def __init__(self, wrkrcon, comm):
                self.wrkrcon = wrkrcon
                if isinstance(wrkrcon, WrkrConfig):
                    self.crewInfo = self.wrkrcon.members
                    self.nodeID = self.wrkrcon.nodeID
                    self.private_key = self.wrkrcon.hostcon.fig['pvtkey']
                    self.public_key = self.wrkrcon.hostcon.fig['pubkey']
                    self.address = self.wrkrcon.hostcon.fig['addr']
                else:
                    self.private_key = self.wrkrcon.fig['pvtkey']
                    self.public_key = self.wrkrcon.fig['pubkey']
                    self.address = self.wrkrcon.fig['addr']
                self.H = HashDigest()
                self.C = comm

        def wrkrSign(self, message):
                signature = self.private_key.sign( message.encode(), hashes.SHA256() )
                stringPK = self.public_key.public_bytes( encoding = serialization.Encoding.PEM, format = serialization.PublicFormat.SubjectPublicKeyInfo )
                address = self.H.generate(str(stringPK))
                retval = {}        
                retval[address] = [stringPK.decode("utf-8"), signature.hex()]
                return retval

        def wrkrVerify(self, sign, message): #sign[address]=[keyString, signature]        
                #get public key from string
                address = ''
                for a in sign.keys():
                        address = a
                key = None
                keyString = sign[address][0]        
                if type(keyString) == str:
                        key = keyString.encode()
                        key = load_pem_public_key(key, backend=default_backend())
                if isinstance(key, dsa.DSAPublicKey):
                        #check if hash of pubkey = address
                        string = key.public_bytes( encoding = serialization.Encoding.PEM, format = serialization.PublicFormat.SubjectPublicKeyInfo )
                        sender = self.H.generate(str(string))
                        if address.startswith('p'):
                                address = address[1:]
                        if sender == address:
                                #sign, message to bytes
                                s = sign[address][1]
                                message = message.encode()
                                s = bytes.fromhex(s)
                                flag = key.verify(s, message, hashes.SHA256() )
                                if flag == None:
                                        return True
                return False

        def toString(self, signature): 
            if signature != None:
                stringSign = {}
                for s in signature.keys():
                        stringSign[s] = json.dumps(signature[s])
                stringSign = json.dumps(stringSign)
                return stringSign
            else:
                return "None"

        def parse(self, stringSign):
            if stringSign == "None":
                return None
            else:
                sign = {}
                stringSign = json.loads(stringSign)
                for s in stringSign.keys():
                        sign[s] = json.loads(stringSign[s])
                return sign

        #in crew broadcast and response
        def sendMessage(self, cnxns, rcvr, tag, msg):
                sender = [self.nodeID, self.address]
                self.C.sendMessage(self.wrkrcon, cnxns, sender, rcvr, tag, tag, msg)

        def getMessage(self, tag):
                return self.C.getMessage(self.wrkrcon, None, tag, tag)

        def sign(self, message, mode): #dictionary address:signature
                if type(message) != str:
                        message.toString()
                sign = {}
                ownSignature = self.wrkrSign(message) 
                if mode == "init":
                        sign = ownSignature
                        cnxns = self.C.connectTo(self.wrkrcon, self.nodeID)
                        if cnxns == None:
                                return None
                        self.sendMessage(cnxns, [self.nodeID], 'crewSign', message)
                        responseSet = self.C.getInCrewResponse(self.wrkrcon, cnxns, "crewSignResp", "crewSignResp")        
                        #print('CS responses :  ', responseSet)
                        self.C.disconnect(cnxns)
                        for resp in responseSet:
                                if resp[2] != "":
                                        s = self.parse(resp[2])
                                        sign[resp[0][1]] = s[resp[0][1]]
                                else:
                                        sign[resp[0][1]] = ""
                        #print(sign)
                        return sign
                elif mode == "resp":
                        #else send sign on message to initiator
                        return ownSignature

        def listener(self):
                #get crewSign req from comm
                while True:
                        c = self.getMessage("crewSign")
                        #if c != None:                #print(c)
                        sender = c[0]
                        msg = c[2]
                        conn = c[3]
                        if sender[1] in self.crewInfo:  #if sender in crew, sign message and send
                                ####IF MESSAGE APPROVED
                                s = self.sign(msg, 'resp')
                                self.sendMessage([conn], sender, 'crewSignResp', self.toString(s))
                        else:
                                self.sendMessage([conn], sender, 'crewSignResp', '')
                        self.C.disconnect([conn])

        def verify(self, sender, message, sign):
                if type(sign) == str:
                        sign = self.parse(sign)
                if len(sender) == 0:        #client
                        return True
                elif len(sender) == 2 or isinstance(sender, str):        #sender=[<crewID>][<address>]
                        return self.wrkrVerify(sign, message)
                else:                                #crewSign, sender=[<crewID>]
                        verifyKeys = self.wrkrcon.getCrewInfo(sender[0])        #dictionary address:pubkey
                        if type(message) != str:
                                message = message.toString()
                        count = 0
                        #check if verifyKey addresses == addresses in sign
                        #print("Verify Key members ::  ",sender[0], verifyKeys)
                        #print("Signature ::  ", sign)
                        if verifyKeys == None:
                            print('verify keys missing. Discovering...')
                            wrkrcon = self.wrkrcon
                            D = Discover(wrkrcon, self.C)
                            crews = D.discoverFetch(sender[0],'root')
                            verifyKeys = crews[0]
                            #verifyKeys = self.wrkrcon.getCrewInfo(nodecrew)
                            
                        if all(addr in verifyKeys for addr in sign) and all(addr in sign for addr in verifyKeys):
                                        for address in sign:
                                                s = {}
                                                s[address] = sign[address]
                                                flag = self.wrkrVerify(s, message)
                                                if flag == True:
                                                        count = count + 1
                                        if count > len(verifyKeys)/2:        #majority signatures verify
                                                return True
                return False







class ClntSign:

        def __init__(self, clntcon):
                self.con = clntcon
                self.H = self.con.hasher

        def wrkrVerify(self, sign, message): #sign[address]=[keyString, signature]        
                #get public key from string
                address = ''
                for a in sign.keys():
                        address = a
                key = None
                keyString = sign[address][0]        
                if type(keyString) == str:
                        key = keyString.encode()
                        key = load_pem_public_key(key, backend=default_backend())
                if isinstance(key, dsa.DSAPublicKey):
                        #check if hash of pubkey = address
                        string = key.public_bytes( encoding = serialization.Encoding.PEM, format = serialization.PublicFormat.SubjectPublicKeyInfo )
                        sender = self.H.generate(str(string))
                        if address.startswith('p'):
                                address = address[1:]
                        if sender == address:
                                #sign, message to bytes
                                s = sign[address][1]
                                message = message.encode()
                                s = bytes.fromhex(s)
                                flag = key.verify(s, message, hashes.SHA256() )
                                if flag == None:
                                        return True
                return False

        def toString(self, signature): 
                stringSign = {}
                for s in signature.keys():
                        stringSign[s] = json.dumps(signature[s])
                stringSign = json.dumps(stringSign)
                return stringSign

        def parse(self, stringSign):
                sign = {}
                stringSign = json.loads(stringSign)
                for s in stringSign.keys():
                        sign[s] = json.loads(stringSign[s])
                return sign

        def verify(self, sender, message, sign):
                if type(sign) == str:
                        sign = self.parse(sign)
                if len(sender) == 0:        #client
                        return True
                elif len(sender) == 2:        #sender=[<crewID>][<address>]
                        return self.wrkrVerify(sign, message)
                else:                                #crewSign, sender=[<crewID>]
                        verifyKeys = self.con.getCrewInfo(sender[0])        #dictionary address:pubkey
                        if type(message) != str:
                                message = message.toString()
                        count = 0
                        #check if verifyKey addresses == addresses in sign
                        if verifyKeys != None:
                                if set(verifyKeys) == set(sign.keys()):
                                        for address in sign:
                                                s = {}
                                                s[address] = sign[address]
                                                flag = self.wrkrVerify(s, message)
                                                if flag == True:
                                                        count = count + 1
                                        if count > len(verifyKeys)/2:        #majority signatures verify
                                                return True
                        else:
                                print('verify key missing')
                return False


#-------------------------------------------------

##TESTING
"""S = CrewSign("1")
print(S.crewInfo)
sign = S.clientSign("message")
print(sign)
v = S.clientVerify(sign, "message")
print(v)
strS = S.toString(sign)
print(strS)
s = S.parse(strS)
print(s)

#sign, listener, verify
v = S.verify(None, "message", sign)
print(v)"""

