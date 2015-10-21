#!/usr/bin/env python

# See LICENSE.txt for details.
# Version: see CHANGELOG file

# Importing default stuff
import select
import socket
import time
import sys
import struct
import getopt
import signal
import types
import string

# Importing specific items. Impacket should be on the system
from impacket import ImpactDecoder, ImpactPacket
from Logger import DB

# Global flag for loop, has to be turned on
RUNNING = 0

def usage():
        """ help function """
        print """
[version 2.2]
The catcher listenes for ICMP reply, Destination Unreachable and Port Unreach
-able packages. it stores some information from these packages in a sqlite DB.
This database can be queried with the simple php frontend.

! The catcher needs to be run with root privileges !

We advise to run the catcher in a screen (http://www.gnu.org/software/screen/)
so you can easily see if it's still running and whether packages are received.
Example:


Optional settings:
-h  --help          Shows this help message
-v                  Adds one to verbosity, use multiple times for more info
-q  --quiet         Default verbosity is 1, this sets it to 0, you will get no
                    output. This option cannot be used in combination with -v.
-D  --Debug         Activates debugging, all packets recieved will be logged to
                    a debug directory."""

def HandleSignal(sig, frame):
        """ Signal handling for quitting with CTRL - C"""
	global RUNNING
	if sig in (signal.SIGINT,signal.SIGTERM):
		#tell main loop to quit
		RUNNING = 0
	else:
		#ignore other signals
		print "SIGNAL PASSED"
		pass

def CatchICMP(conf):
        """ Main loop for catching packets """
	global RUNNING

	# Open a raw socket. Special permissions are usually required.
	s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
	s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

	# Open a database object, the object will initialize a full db structure.
	datalog = DB()

	# Timestamp to start with
	ts_main = time.time()

	# Set some signals.
	oldInt = signal.signal(signal.SIGINT,HandleSignal)
	oldTerm = signal.signal(signal.SIGTERM,HandleSignal)
	oldHup = signal.signal(signal.SIGHUP,HandleSignal)

        # We are entering the main indefinite loop
	RUNNING = 1
	while RUNNING:
		# Wait for incoming replies.
		if s in select.select([s],[],[],1)[0]:
			reply = s.recvfrom(2000)[0]

			# Use ImpactDecoder to reconstruct the packet hierarchy.
			rip = ImpactDecoder.IPDecoder().decode(reply)
			# Extract the ICMP packet from its container (the IP packet).
			ricmp = rip.child()
			
			################################
			# Types of received packages
			# 1, ICMP Reply
			# 2, DU ICMP
			# 3, DU UDP
			# TODO: DU PU UDP (Port unreach)
			################################
	
			# If type is ICMP Reply
			if ricmp.ICMP_ECHOREPLY == ricmp.get_icmp_type():
				data = ricmp.get_data_as_string()
				insert_ts = datalog.insert( 'catch', socket.inet_ntoa(data[0:4]), rip.get_ip_src(),\
						socket.ntohs(struct.unpack('H',data[4:6])[0]), socket.ntohs(struct.unpack('H',data[6:8])[0]), "ICMP REPLY" )
                                
                                # block of code for writing verbose output
				if conf['verbose'] in range(1,3):
					sys.stdout.write(".")
					sys.stdout.flush()
				if conf['verbose'] > 2:
					print "Session:%6s | Victim:%16s | Gateway:%16s | Unique:%16f | Type:%12s" % \
						(socket.ntohs(struct.unpack('H',data[4:6])[0]),socket.inet_ntoa(data[0:4]),rip.get_ip_src(),\
							socket.ntohs(struct.unpack('H',data[6:8])[0]), "ICMP REPLY")

			# If we're dealing with a DU packet		
			if ricmp.ICMP_UNREACH == ricmp.get_icmp_type():
				data = ricmp.get_data_as_string()

                                # If the DU is a reply to ICMP	
				if  struct.unpack('c',data[9:10])[0] == '\x01':
					insert_ts = datalog.insert( 'catch', socket.inet_ntoa(data[16:20]), rip.get_ip_src(),\
						socket.ntohs(struct.unpack('H',data[32:34])[0]), socket.ntohs(struct.unpack('H',data[34:36])[0]), "DU ICMP" )
                                        
                                        # block of code for writing verbose output
					if conf['verbose'] in range(1,3):
						sys.stdout.write(".")
						sys.stdout.flush()
                                	if conf['verbose'] > 2:
						print "Session:%6s | Victim:%16s | Gateway:%16s | Unique:%16f | Type:%12s" % \
							(socket.ntohs(struct.unpack('H',data[32:34])[0]),socket.inet_ntoa(data[16:20]),rip.get_ip_src(),\
								socket.ntohs(struct.unpack('H',data[34:36])[0]), "DU ICMP" )

                                # If the DU is a reply to UDP
				elif struct.unpack('c',data[9:10])[0] == '\x11':
					insert_ts = datalog.insert( 'catch', socket.inet_ntoa(data[16:20]), rip.get_ip_src(),\
				        	socket.ntohs(struct.unpack('H',data[20:22])[0]), socket.ntohs(struct.unpack('H',data[4:6])[0]), "DU UDP" )

                                        # block of code for writing verbose output
                                	if conf['verbose'] in range(1,3):
						sys.stdout.write(".")
						sys.stdout.flush()
                                	if conf['verbose'] > 2:
						print "Session:%6s | Victim:%16s | Gateway:%16s | Unique:%16f | Type:%12s" % \
							(socket.ntohs(struct.unpack('H',data[20:22])[0]),socket.inet_ntoa(data[16:20]),rip.get_ip_src(),\
								socket.ntohs(struct.unpack('H',data[4:6])[0]), "DU UDP" )

				else:
					print struct.unpack('c',data[9:10])
					print ("consider implementing this new type of DU package sinds we hit it.")

                        # If we're in debug mode we need to do more	
			if conf['debug']:
				# We need to open a new file and write the full packet to it
				fp = open("debug/%f.pckt" % insert_ts , "w")
				fp.write( reply )
				fp.flush()
				fp.close()

		# We only commit to database when needed for performance reasons
		if( (time.time()-ts_main) > 10):
			datalog.connection.commit()
			ts_main = time.time()
			
                        # block of code for writing verbose output
                        if conf['verbose'] in range (2,3):
                        	sys.stdout.write("#")
                        	sys.stdout.flush()
			if conf['verbose'] > 2:
				print "  database commit done, 10 seconds since last commit have passed!"

	print "Succesfully stopped"
	# Reset the signalhandlers
	signal.signal(signal.SIGINT,oldInt)
	signal.signal(signal.SIGINT,oldTerm)
	signal.signal(signal.SIGINT,oldHup)
	
	datalog.close()

def main(argv):
        """Main function, reads arguments, does sanity checks and will start server loop """

	# Some default configuration value's
	conf = {"verbose":1,"debug":0,"quiet":0}

        # Code block for handeling options
        try:
                optlist, list = getopt.getopt(argv[1:],"qhvD", ["quiet","help","debug"])
        except getopt.GetoptError, err:
                # Print helpinfo and exit
                print str(err) # Will tell what option isn't recognized
                usage()
                sys.exit(1)
        for opt in optlist:
                if opt[0] == "-v":
                        conf["verbose"] = conf["verbose"] + 1
                elif opt[0] in ("-q","--quiet"):
                        conf["quiet"] = True
                elif opt[0] in ("-D","--debug"):
                        conf["debug"] = 1
                elif opt[0] in ("-h","--help"):
                        usage()
                        sys.exit(0)

	# Sanity check, we only have one! Default verbose is 1, quiet makes it 0. -v and -q should not be used together
	if conf['quiet']:
		if conf['verbose'] > 1:
			print "Please don't use -q or --quiet in combination with -v"
			sys.exit(0)
		conf['verbose'] = 0

        # Block of code for writing verbose output
	if conf['verbose'] > 0: 
		print "Catcher running with verbosity %d and debug-level %d" % (conf['verbose'],conf['debug'])

	# Start the server loop
	CatchICMP(conf)

if __name__ == "__main__":
        main(sys.argv)

