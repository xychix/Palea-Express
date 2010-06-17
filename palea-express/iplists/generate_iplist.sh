#/bin/bash

nmap -sL -n $1 | cut -d " " -f 2 | grep -e ".*\..*\..*\..*" 
