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

import os
import gst
from common import useful
from common.config import cfg
from common.gstPlayer import player

# A global current tags list for reading.
curTags = [None, None]

def getCurTags():
	## Gets the currently playing file's tags.
	# If the first item isn't the current playing file, the tags are old, so return None.
	return curTags[1] if (curTags[0] == player.getURI()) else None

def getDispTitle(tags):
	# Set the tags for the current file.
	global curTags
	curTags = [player.getURI(), tags]
	# Flag that no tags have been added.
	noneAdded = True
	# Initiate the windows title.
	winTitle = ""
	for x in useful.tagsToTuple(cfg.getStr('gui/tagsyntax')):
		# For all the items in the list produced by tagsToTuple.
		# New string = the associated tag if it's a tag, otherwise just the string.
		# Remember in each x, [0] is True if [1] is a tag, False if it's not.
		try:
			nStr = tags[x[1]] if (x[0]) else x[1]
		except KeyError:
			nStr = None
		if (nStr):
			# If there was a string.
			# Flag that a tag has been added if it's a tag.
			if (x[0]): noneAdded = False
			# Add the string to the new window title.
			winTitle += nStr
	# If at least one tag was added, return the title, otherwise fall
	# back to the filename function.
	if (not noneAdded):
		return winTitle
	else:
		file = player.getURI()
		if (os.sep in file): file = file.split(os.sep)[-1]
		# Remove the file extenstion (wow, this is messy).
		if ('.' in file): file = file[:-(len(file.split('.')[-1]) + 1)]
		return file

def getDispTitleFile(uri):
	## A function that will in future read tags from a file URI.
	pass


class FileTag:
	lock = False
	queue = []
	funcDic = {}
	
	def file(self, uri, function):
		self.queue.append(uri)
		self.funcDic[uri] = function
		if (not self.lock): self.nextTrack()
	
	def nextTrack(self):
		if (not len(queue)):
			lock = False
			return
		next = self.queue[0]
		self.queue = self.queue[1:]
		self.player.set_property('uri', uri)
		self.player.set_state(gst.STATE_PAUSED)
	
	def onMessage(self, bus, message):
		if (message.type not in [gst.MESSAGE_ERROR, gst.MESSAGE_TAG]):
			uri = self.player.get_property('uri')
			if (message.type == gst.MESSAGE_TAG):
				self.funcDic[uri](uri, message.parse_tag())
				self.player.set_state(gst.STATE_READY)
			
			del self.funcDic[uri]
			self.nextTrack()
	
	
	def __init__(self):
		self.player = gst.element_factory_make('playbin')
		self.player.set_property('video-sink', gst.element_factory_make('fakesink'))
		self.player.set_property('audio-sink', gst.element_factory_make('fakesink'))
		
		bus = self.player.get_bus()
		bus.add_signal_watch()
		bus.connect('message', self.onMessage)

fileTag = FileTag()
