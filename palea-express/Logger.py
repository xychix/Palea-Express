#!/usr/bin/env python

# See LICENSE.txt for details.
# Version see CHANGELOG file

import time
from pysqlite2 import dbapi2 as sqlite

class DB:
	""" Simple thin DB class for inserting into db """
	def __init__(self,filename='../var/palea.db'): #adjust this location of DB when needed
		self.connection = sqlite.connect(filename)
		self.cursor = self.connection.cursor()
		# We need to create a table for incoming packets
		self.cursor.execute('CREATE TABLE IF NOT EXISTS catch(id INTEGER PRIMARY KEY, timestamp REAL, victim VARCHAR(50), gateway VARCHAR(50), session INT, uniqueId REAL, type VARCHAR(50) )' )	
	
	def insert(self,table,victim,source,session,uniqueId,type):
                """ Insert a packet into the database """
		ts = time.time()
		sql = "INSERT INTO %s VALUES ( NULL,%f,?,?,?,?,? )" % (table, ts)
		self.cursor.execute(sql,( victim,source,session,uniqueId,type ) )
		return ts

	def close(self):
                """ commit before closing """
		self.connection.commit()
