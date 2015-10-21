#!/usr/bin/env python

# See LICENSE.txt for details.
# Version see CHANGELOG file

import socket
import re

def isValidIp(ip):
        """ A regular expression for checking the validity of an IPv4 address """
	pattern = r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
	if re.match(pattern, ip):
		return True
	else:
		return False	
