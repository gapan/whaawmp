#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  Whaaw! Media Player for playing any type of media.
#  Copyright © 2007-2008, Jeff Bailes <thepizzaking@gmail.com>
#       This file is part of Whaaw! Media Player (whaawmp)
#
#       whaawmp is free software: you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation, either version 3 of the Licence, or
#       (at your option) any later version.
#       
#       whaawmp is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
from optparse import OptionParser

import gobject
gobject.threads_init()
import gettext
gettext.install('whaawmp', unicode=1)
from common import useful

# Check that at least python 2.5 is running.
if (sys.version_info < (2, 5)):
	print _('Cannot continue, python version must be at least 2.5.')
	sys.exit(1)

# If gobject version < 2.14 we need to define timeout_add_seconds.
if (gobject.glib_version < (2,14)):
	print _("Old timer method used, since glib version is pre-2.14")
	# Define our own timeout_add wrapper.
	gobject.timeout_add_seconds = lambda *args: gobject.timeout_add(useful.sToms(args[0]), *args[1:])

# Have to manually check for help here, otherwise gstreamer prints out its own help.
HELP = False
for x in ['--help', '-h']:
	# If -h or --help is there, help is true (also remove it so gstreamer doesn't get it)
	if (x in sys.argv):
		HELP = True
		sys.argv.remove(x)

if ('--version' in sys.argv):
		# If --version, print out the version, then quit.
		print '%s - %s' % (useful.lName, useful.version)
		sys.exit(0)


from gui import main as whaawmp
from common import config
from common.dbusBus import initBus

# Change the process name (only for python >= 2.5, or if ctypes installed)
# Though, this program requires 2.5 anyway?:
try:
	import ctypes
	libc = ctypes.CDLL('libc.so.6')
	libc.prctl(15, useful.sName, 0, 0)
except:
	pass

class main:

	def __init__(self):
		## Initialises everything.
		# Option Parser
		usage = "\n  " + useful.sName + _(" [options] filename")
		(options, args) = config.clparser(OptionParser(usage=usage, prog=useful.sName)).parseArgs(HELP)
		
		# Check if whaawmp is already running and send dbus messages if it is.
		# Quit if the command is one it should quit after.
		if (initBus(options, args).quitAfter): sys.exit()

		# Creates the window.
		self.mainWindow = whaawmp.mainWindow(self, options, args)
		
		return


main()
