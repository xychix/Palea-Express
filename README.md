Palea
==========

I assume you've red the PDF's on the techniques and goal of Palea. It's 
included in this git. It is written for a PoC I had before conding it all
together.

Download is all and run ./thrower.py -h as root. You will get the help 
listing there. (make sure you have all the stuff you need, including Impacket)

In order to start throwing packages in the right directions with the right
options you'll need a file containing all the ip's you want to target. I've
included an nmap script in order to generate such a list from other notations.
Please open de list in your favourite text editor and ensure that your own
network and broadcast address are not in the list. Impacket, our packetlib
appears to have issues with those. 

How will you get the results from Palea? 

	You've downloaded the sourcecode together with a simple webinterface once
   	you've placed this on a server with apache or any other running webserver
	you can be your own 'catcher' you'd need to place this catcher in the net-
	work (or internet) you wan't to detect leakage to. This solution however
	will require some technical knowlegde. In this paragraph I explain the
	steps I took to get it al running on a brand new debian installataion.
	This example installation however doesn't deal with SSL nor with virtual-
	hosts. It assumes a stand alone debian for this purpose only.

	Installation steps
	
	apt-get install openssh-server

	apt-get install screen python sqlite sqlite3 python-impacket python-pcapy 
	apache2 nmap openssl libssl0.9.8 libapache2-mod-php5 rdate php5-sqlite php-db 
	python-pysqlite2

	mkdir /home/www-data
	chown -R www-data:www-data /home/www-data
	unpack palea.tgz in /home/www-data it contains a dir www, set docroot to here
	vim /etc/apache2/sites-enabled/000-default
	edit line 4 and +/- 10.. change /var/www in /home/www-data/www
	apache2ctl restart
	chown -R www-data:www-data /home/www-data

	schreen -mS catcher
	[inside screen]
	cd /home/www-data/palea-express
	./catcher
	[press CTRL+a  then  d   to detach]
	#following line gives you your IP's
	ifconfig|grep 'inet addr'|awk '{print $2}'|sed 's/addr://g'

	#use this IP in the launch of a hartbeat message (sesion 0)
	/home/www-data/palea-express/thrower.py -t I -s 0 -i /home/www-data/palea-express/iplists/hb.ips -c $ip

	now visit http://$ip/palea/

	you should see an overview with a heartbeat alive message.