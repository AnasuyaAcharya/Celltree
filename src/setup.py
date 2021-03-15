import json
import os
import sys
from pathlib import Path
from CTHost import Host
from CTClnt import Clnt

topdirpath = Path(__file__).resolve().parents[1]
rundir = str(topdirpath) + "/run/"
Adir = rundir + "addr/"
Hdir = rundir + "Hosts/"
Cdir = rundir + "Clnt/"

if len(sys.argv) != 2:
    print("A single setup file expected")
    proceed = input("Delete all keys and address files? [y/N] ")
    if proceed == 'y':
        os.system("rm -v " + Adir + "addr.txt")
        os.system("rm -v " + Adir + "rootCrew.txt")
        for h in Path(Hdir).iterdir():
            if not h.is_dir():
                continue
            os.system("rm -vr " + str(h) + "/key" )
else:
    # read a setup dictionary: { "node": [ "host",... ], ... }
    setupfile = sys.argv[1]
    hostsOf = {}
    with open(setupfile, "r") as f:
        hostsOf = json.load(f)

    # make a reverse dictionary 
    crewsOf = {}
    for node, hosts in hostsOf.items():
        for host in hosts:
            crewsOf.setdefault(host,set())
            crewsOf[host].add(node)
    # populate addr.txt
    addrOf = {}
    addr = {}
    for host in crewsOf.keys():
        try:
            with open(Hdir + host + "/key/addr.txt", "r") as f:
                addrOf[host] = json.load(f)
                addr.update(addrOf[host])
        except Exception as e:
            print("Host", host, " has no key? Error: " + str(e))
    with open(Adir + "addr.txt", "w") as f:
        json.dump(addr,f)
    #print(addrOf)
    #print(addr)
    # populate wrkrList
    for host in crewsOf.keys():
        hostwrkdir = Hdir + host + "/wrk/"
        os.system("mkdir -p " + hostwrkdir)
        nodeList = ""
        for node in crewsOf[host]:
            nodeList = nodeList + node + "\n"
        with open(hostwrkdir + "wrkrList.txt", "w") as f:
            f.write(nodeList)

    # populate members
    for node in hostsOf.keys():
        hs = hostsOf[node]
        members = []
        for host in hostsOf[node]:
            #with open(Hdir + host + "/key/pubkey.txt", "r") as f:
            #    m = json.load(f)
            #m.append(addrOf[host])
            #m = addrOf[host]
            for a in addrOf[host].keys():
                members.append(a)
        #print(members)
        for host in hostsOf[node]:
            wrkdir = Hdir + host + "/wrk/" + node + "/"
            os.system("mkdir -p " + wrkdir)
            with open(wrkdir + "members.txt", "w") as f:
                json.dump(members,f)
            os.system("mkdir -p " +  Hdir + host + "/crews/")
            for h in crewsOf.keys():
                os.system("cp -v " + wrkdir + "members.txt " +  Hdir + h + "/crews/" + node)

        # populate rootCrew
        if node == 'root':
            with open(Adir + "rootCrew.txt", "w") as f:
                json.dump(members,f)
            
