#!/usr/bin/python3
import sys
from CTHost import Host
from CTClnt import Clnt
from pathlib import Path

srcdir = str(Path(__file__).resolve().parents[0])
rundir = str(Path(__file__).resolve().parents[1]) + "/run/"
Hdir = rundir + "Hosts/"
Cdir = rundir + "Clnt/"

role = sys.argv[1]
if role.startswith('h'):
    name=sys.argv[2]
    hostdir=Hdir + name
    Host(hostdir)
elif role.startswith('c'):
    Clnt(Cdir)
else:
    print('Usage: main.py host <name> or main.py client')
