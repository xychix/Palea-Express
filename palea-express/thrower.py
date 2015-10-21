#!/usr/bin/env python

# See LICENSE.txt for details.
# Version See CHANGELOG file

# imports of default stuff
import os
import signal
import string
import urllib
import types
import getopt
import struct
import select
import socket
import time
import sys

# importing impacket
from impacket import ImpactDecoder, ImpactPacket

# importing own function
import Functions as f

def usage():
        """ help function, might need an update """
        print """
[version 2.2]
The thrower sends out packages to systems that will try and reply to the 
palea catcher. 
Examepl:
thrower.py -vv -d 0.3 -t UI -s 1 -i ./iplists/hartbeat.ips -c "YOUR IP"
Atleast use the options -i -s and -c

Required settings:
-i  --input=        this should point to the list of ip's you wan't to target
-s  --session=      The sessionnumber (to identify your packages when recieved
                    by the cathcer. choose between 1 and 65 535, 0 may be used 
                    as a hartbeat monitor.

Optional settings:
-c  --catcher=      this is the ipadress of the catcher.
-d  --delay=        A delay may be specified for slow networks, you don't wan't
                    to overload the network, preventing packages from reaching
                    it's target.
-h  --help=         Shows this help message
-o  --output=       this points to the output file for a logging of all packets
                    sent during this session
-t  --tests=        U for UDP, I for ICMP or UI for both.
-v                  Adds one to verbosity, use multiple times for more info
"""

def SendUDP(srcIP,dstIP,sessionNr,counter):
        """ SendUDP sends a specially crafted UDP packet """

        # prepare the IP part
	ip = ImpactPacket.IP()
	ip.set_ip_src(srcIP)
	ip.set_ip_dst(dstIP)
	ip.set_ip_id(counter)
	
        # prepare the ICMP part
	udp = ImpactPacket.UDP()
	udp.set_uh_sport(sessionNr)
	udp.set_uh_dport(53)

	#auto generate checksum
	udp.set_uh_sum(0)
	udp.auto_checksum = 1

        # prepare the payload
        # put the target IP and the session number in the payload also for later recovery
        data = socket.inet_aton(dstIP)+struct.pack('H',socket.htons(sessionNr))+struct.pack('H',socket.htons(counter))
	
        # compose the total packet IP / icmp / payload
        udp.contains(ImpactPacket.Data(data))
	ip.contains(udp)

	# Open a raw socket. Special permissions are usually required.
	s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
	s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

	# and set it free
	s.sendto(ip.get_packet(), (dstIP, 0))
	
	# return timestamp for further reference
	return time.time()

def SendICMP(srcIP,dstIP,sessionNr,counter):
        """ SendICMP sends a specially crafted ICMP packet """
        
        # prepare the IP part
	ip = ImpactPacket.IP()
	ip.set_ip_src(srcIP)
	ip.set_ip_dst(dstIP)
	#this counter isn't used.
	ip.set_ip_id(counter)
	
        # prepare the ICMP part
	icmp = ImpactPacket.ICMP()
	#is used to read out uniquenumber in case of DU ICMP reply
	icmp.set_icmp_id(sessionNr)
	#is used to read out sessionnumber in case of DU ICMP reply
	icmp.set_icmp_seq(counter)

	#auto generate checksum
	icmp.set_icmp_cksum(0)
	icmp.auto_checksum = 1
	icmp.set_icmp_type(icmp.ICMP_ECHO)

        # prepare the payload
        # put the target IP and the sequence number in the payload also for later recovery
        data = socket.inet_aton(dstIP)+struct.pack('H',socket.htons(sessionNr))+struct.pack('H',socket.htons(counter))
	
	# compose the total packet IP / icmp / payload
        icmp.contains(ImpactPacket.Data(data))
	ip.contains(icmp)

	# Open a raw socket. Special permissions are usually required.
	s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
	s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

	# and set it free
	s.sendto(ip.get_packet(), (dstIP, 0))
	
	# return timestamp for further reference
	return time.time()

def main(argv):
        """ main function shooting out packets based on a list of ip's and commandline options """

	#let's keep some config values in conf dict
	conf = {"verbose":0,"session":"NULL","inputfile":"iplist.txt","outputfile":"NULL","catcher":"NULL","tests":"IU","delay":0}
        "FaF: let's shoot the buggers out"

	# Lets catch the starttime early
	starttime = time.time()

        # Gathering all the commandline options and process them in the conf dict.
	try:
		optlist, list = getopt.getopt(argv[1:],"hvs:i:c:o:t:d:", ["help","session=","input=","catcher=","output=","tests=","delay="])
	except getopt.GetoptError, err:
		#print helpinfo and exit
		print str(err) #will tell what option isn't recognized
		usage()
		sys.exit(1)
	for opt in optlist:
		if opt[0] == "-v":
			conf["verbose"] = conf["verbose"] + 1
		elif opt[0] in ("-s","--session"):
			conf["session"] = opt[1]
		elif opt[0] in ("-i","--input"):
			conf["inputfile"] = opt[1]
		elif opt[0] in ("-o","--output"):
			conf["outputfile"] = opt[1]
		elif opt[0] in ("-c","--catcher"):
			conf["catcher"] = opt[1]
		elif opt[0] in ("-t","--tests"):
			conf["tests"] = opt[1]
		elif opt[0] in ("-d","--delay"):
			conf["delay"] = opt[1]
		elif opt[0] in ("-h","--help"):
			usage()
			sys.exit(0)

        # Some information for our verbose users
	if conf["verbose"] > 1:
		print "----------------------------------------"
		print "-- Starting thrower"
		print ""
		print "Using parameters:"
		print "- verbosity  is: %s" % (conf["verbose"])
		print "- session    is: %s" % (conf["session"])
		print "- delay      is: %s" % (conf["delay"])
		print "- inputfile  is: %s" % (conf["inputfile"])
		print "- outputfile is: %s" % (conf["outputfile"])
		print "- catcher    is: %s" % (conf["catcher"])
		print "- tests     are: %s" % (conf["tests"])
		print ""	
		print "----------------------------------------"
	
	
	# We've gonna do some sanity checks here, lets use a bool to see if we need to quit
	# DANGER: we assume all is ok until we decide it's not, actually we want 'deny by default'
	quit = False
	
        # Recent hack to ensure we can work without output (for the heartbeat)
        if (conf['outputfile'] is "NULL"):
                conf['outputfile'] = "/dev/null"
	# test is output file exists and then add extention number if file exists
	elif os.path.exists(conf["outputfile"]):
		ext_nr = 1
		while os.path.exists(conf["outputfile"] + "." + str(ext_nr)):
			ext_nr = ext_nr +1
		conf["outputfile"] = conf["outputfile"] + "." + str(ext_nr)
		
	# Opening list of IP's
	try:		
		input_fp = open(conf["inputfile"], "r")
	except IOError, (ErrorNumber,ErrorMessage):
		if ErrorNumber == 2:    # file not found, most likely
			print "- Sorry, file \"%s\" not found, please feed me a file with only ipaddresses" % (conf["inputfile"])
		else:                   # some other file error triggered
			print "- Congrats, you managed to trigger errornumber %s" % (ErrorNumber)
			print "     " + ErrorMessage
		sys.exit(1)
	if conf["verbose"] > 1 : print "- %s opened" % conf["inputfile"]

	# Validate IP for catcher
	if f.isValidIp(conf["catcher"]) == False :
		print "- %s (Catcher) is not a valid IP address!" % (conf["catcher"])
		quit = True

        # Sanity checking on some numeric values
	try:
		float(conf["delay"])
		if (float(conf["delay"]) < 0 ) or (float(conf["delay"]) > 60 ) :
			raise Exception("Out of range! timing needs to be between 0.000 and 60.000 seconds.")
	except:
		print "- %s is not a valid delay value in seconds, choose between 0.000 and 60.000 seconds." % (conf["delay"])
		quit = True

	try:
		int(conf["session"])
		if int(conf["session"]) not in range(0,65535):
			raise Exception("Out of range!")
	except:
		print "- %s is not a valid session ID, choose between 0 and 65535." % (conf["session"])
		quit = True
		
	# Read the IP file and test all ip's for validity	
	ips = input_fp.readlines()
	input_fp.close()

	for ip in ips:
		#check if all ip's provided are ok
		if f.isValidIp(ip) == False :
			quit = True
			print "- %s is not a valid IP address!" % (ip.strip())
		
	# Opening the determined output filename if we're not quitting already
	if quit == False:
		try:		
			output_fp = open(conf["outputfile"], "w")
		except IOError, (ErrorNumber,ErrorMessage):
			print "- Congrats, you managed to trigger errornumber %s" % (ErrorNumber)
			print "     " + ErrorMessage
			sys.exit(1)
		if conf["verbose"] > 1 : print "- %s opened" % conf["outputfile"]

	# See if real tests are send out, else we need to tell user it is a dry run
	if ("U" not in conf["tests"]) and ("I" not in conf["tests"]):
		print "No tests selected! use -t IU  (ICMP UDP)"
		quit = True
	
	# Number of checks done, lets see if we need to quit	
	if quit:
		print ""
                print "One of more errors in your command line options"
		print "Please get your stuff together! I'm quitting!"
		sys.exit(1)

        # We set a counter to keep count of packets send
	counter = 0
 	for ip in ips:	
		time.sleep(float(conf["delay"]))
                # If we configured I, we need to send ICMP packets
		if "I" in conf["tests"]:
			counter = counter + 1
			unique_id = SendICMP(conf["catcher"], ip, int(conf["session"]), counter )
               		# writing csv    id;unique;session;catcher;victim;
                	output_fp.write("NULL;%f;%s;%s;%s;%s\n" % (unique_id,conf["session"],conf["catcher"],ip.strip(),"ICMP") )
			if conf["verbose"] > 2:
				print "  - timstamp: %10f | victim: %16s | catcher: %16s | session: %4s | unique: %16f | test:%5s"\
					% (unique_id,ip.strip(),conf["catcher"],conf["session"],counter,"ICMP")

                # IF we configured U, we need to send UDP packets
		if "U" in conf["tests"]:
			counter = counter +1
			unique_id = SendUDP(conf["catcher"], ip, int(conf["session"]), counter )
        	        # writing csv    id;unique;session;catcher;victim;
	                output_fp.write("NULL;%f;%s;%s;%s;%s\n" % (unique_id,conf["session"],conf["catcher"],ip.strip(),"UDP") )
        	        if conf["verbose"] > 2:
                	        print "  - timstamp: %10f | victim: %16s | catcher: %16s | session: %4s | unique: %16f | test:%5s" \
					% (unique_id,ip.strip(),conf["catcher"],conf["session"],counter,"UDP")

	        # Verbosety: printing a U or an I for each packet sent.	
		if conf["verbose"] in range(1,3):
			sys.stdout.write(conf["tests"])
			sys.stdout.flush()
		# If our counter approaches the max it will reset, NOTE received reply's might not be unique anymore!
                if counter > 65000: 
			counter = 1
                        # Verbosety printing
			if conf["verbose"] in range(1,3): sys.stdout.write("1")
			if conf["verbose"] > 2: print " - Resetting unique counter"
	if conf["verbose"] > 0 : print "\nFinished sending %d packets in %s seconds" % (counter , (time.time() - starttime))
		
if __name__ == "__main__":
        main(sys.argv)
