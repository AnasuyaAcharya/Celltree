# Celltree

Refer to the documentation for the details of the code.

1. create a setup file:
	'setup.txt':
		* should contain a dictionary of the form <nodeID>: [<list of host IDs>]
		* must contain the "root" node
		* may contain other nodes: forming a(n incomplete) tree from the root
		* an example is given in 'example-setup.txt'

	* This file is used to initialize the Celltree.


2. reset the Celltree:
	> python3 setup.py
	> A single setup file expected
	> Delete all keys and address files? [y/N]
	> y

	* This erases the state of a previously existing Celltree demo.


3. initialize new Celltree:
	> python3 setup.py setup.txt

	* Uses the setup file and creates all the hosts whose IDs are given. Within the hosts, creates the state for all the crews it is part of.


4. run host:
	> python3 main.py host 1


5. run client:
	> python3 main.py client
