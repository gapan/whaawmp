# -*- coding: utf-8 -*-

#  Other Dialogues
#  Copyright © 2007, Jeff Bailes <thepizzaking@gmail.com>
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

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade, gobject
import os, urllib

from common import mutagenTagger as tagger

class queues():
	mnuiWidget = None
	
	mnuiSet = lambda self, shown: self.mnuiWidget.set_active(shown)
	length = lambda self: len(self.list)
	
	def close(self, widget, event):
		self.hide()
		return True
	
	def toggle(self, toShow=None):
		if (toShow is None): toShow = not open
		if (toShow):
			self.show()
		else:
			self.hide()
	
	def show(self, force=False):
		self.mnuiSet(True)
		open = True
		self.window.show()
	
	def hide(self, force=False):
		self.mnuiSet(False)
		open = False
		self.window.hide()
	
	def append(self, item):
		row = self.list.append()
		self.list.set_value(row, 0, item)
		self.list.set_value(row, 1, tagger.getDispTitle(item))
	
	def clear(self):
		self.list.clear()
	
	def getNextLocRemove(self):
		try:
			path = self.list[0][0]
			self.remove(0)
			return path
		except IndexError:
			return None
	
	remove = lambda self, index: self.list.remove(self.list.get_iter(index))
	
	def enqueueDropped(self, widget, context, x, y, selection_data, info, time):
		## Adds dropped files to the end of the queue.
		# Split the files.
		uris = selection_data.data.strip().split()
		# Add all the items to the queue.
		for x in uris:
			uri = urllib.url2pathname(x)
			self.append(uri)
		# Finish the drag.
		context.finish(True, False, time)
	
	def __init__(self):
		open = False
		self.list = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
		self.window = gtk.Window()
		self.window.set_title(_("Queue"))
		self.window.resize(250,250)
		self.window.connect('delete-event', self.close)
		self.window.drag_dest_set(gtk.DEST_DEFAULT_ALL, [("text/uri-list", 0, 0)], gtk.gdk.ACTION_COPY)
		self.window.connect('drag-data-received', self.enqueueDropped)
		tree = gtk.TreeView(self.list)
		renderer = gtk.CellRendererText()
		column = gtk.TreeViewColumn(_("Track"), renderer, text=1)
		tree.append_column(column)
		tree.set_reorderable(True)
		scrolly = gtk.ScrolledWindow()
		scrolly.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		scrolly.add(tree)
		scrolly.show()
		vBox = gtk.VBox()
		vBox.pack_start(scrolly)
		vBox.show()
		self.window.add(vBox)
		tree.show()

queue = queues()
