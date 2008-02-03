# -*- coding: utf-8 -*-

#  An interface for tagging (gstreamer).
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

import gst
from common import useful
from common.config import cfg

def getDispTitle(tags):
	# Flag that no tags have been added.
	noneAdded = True
	# Initiate the windows title.
	winTitle = ""
	for x in useful.tagsToTuple(cfg.getStr('gui/tagsyntax')):
		# For all the items in the list produced by tagsToTuple.
		# New string = the associated tag if it's a tag, otherwise just the string.
		# Remember in each x, [0] is True if [1] is a tag, False if it's not.
		nStr = tags[x[1]] if (x[0]) else x[1]
		if (nStr):
			# If there was a string.
			# Flag that a tag has been added if it's a tag.
			if (x[0]): noneAdded = False
			# Add the string to the new window title.
			winTitle += nStr
	# If at least one tag was added, return the title, otherwise fall
	# back to the filename function.
	return winTitle if (not noneAdded) else useful.lName

def getDispTitleFile(uri):
	pass
