#!/usr/bin/env python

# Configuration Backend
# Copyright (C) 2007, Jeff Bailes <thepizzaking@gmail.com>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.


import os, sys
from ConfigParser import SafeConfigParser
import lists

class config:
	def save(self):
		## Saves the configuration file.
		f = open(self.loc, "w")
		self.config.write(f)
		f.close()
	
	
	def splitOpt(self, option):
		if ('/' not in option):
			print 'Error!! No slash in option, something bad happened!'
			sys.exit()
		return option.split('/')
	
	
	def get(self, option, default):
		## Gets a configuration option.
		section, option = self.splitOpt(option)
		# Try to get it, if it fails (option doesn't exist, set the 
		# option to the default value passed and return it.
		try:
			return self.config.get(section, option)
		except:
			self.set(section, option, default)
			return default
	
	
	def set(self, option, value):
		## Sets the option value to that passed.
		section, option = self.splitOpt(option)
		if (section not in self.config.sections()):
			# If the section doesn't exist, add it.
			self.config.add_section(section)
		
		# Set the option to the value.
		self.config.set(section, option, str(value))
	
	
	def getStr(self, option, default):
		## Returns the option as a string, even though this already happens.
		return self.get(option, default)
			
	
	def getInt(self, option, default):
		## Returns an option as an integer.
		res = self.get(option, default)
		# If the type won't go directly to an integer, try a float first.
		try:
			return int(res)
		except:
			return int(float(res))

	
	def getFloat(self, option, default):
		# Returns the requested option as a float.
		return float(self.get(option, default))
	
	
	def getBool(self, option, default):
		# Returns the requested option as a bool.
		res = self.get(option, default)
		if (res in ['False', 'false', '0', 'None']):
			return False
		return True
		
	
	def prepareConfDir(self, dir):
		## Checks if the config directory exists, if not, create it.
		if (not os.path.isdir(dir)):
			os.makedirs(dir)
	
	
	def __init__(self, dir, file):
		## Preparation.
		# Make sure the config directory exists.
		self.prepareConfDir(dir)
		# Create a config parser.
		self.config = SafeConfigParser()
		# Set the config files location.
		self.loc = dir + os.sep + file
		
		# Open the config file.
		self.config.read(self.loc)



class clparser:
	## Command line parsing.
	def __init__(self, parser):
		self.parser = parser
	
	def parseArgs(self, HELP):
		# Add the options to the parser.
		self.addOptions()
		# If help was requested, print it, then exit.
		if (HELP):
			self.parser.print_help()
			sys.exit()
		# Parse the arguments and return the result.
		return self.parser.parse_args()
	
	
	def addOptions(self):
		# Activate fullscreen (only if playing a video)
		self.parser.add_option("-f", "--fullscreen",
		                       action="store_true", dest="fullscreen", default=False,
		                       help="Play the file in fullscreen mode.")
		self.parser.add_option("--force",
		                       action="store_true", dest="force", default=False,
		                       help="Force start (if not being run by script)")
		
