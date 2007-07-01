#!/usr/bin/env python

#  Whaaw! Media Player for playing any type of media.
#  Copyright (C) 2007, Jeff Bailes <thepizzaking@gmail.com>
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

import sys, os, os.path, urllib
import pygtk
pygtk.require('2.0')
import gtk, gobject
import gtk.glade
from optparse import OptionParser

import config
import player
import dialogues

whaawmpName='whaawmp'
whaawmpVersion='0.0.2'

# Change the process name (only for python >= 2.5, or if ctypes installed):
try:
	import ctypes
	libc = ctypes.CDLL('libc.so.6')
	libc.prctl(15, whaawmpName, 0, 0)
except:
	pass

class main:
	gladefile = "whaawmp.glade"
	
	def quit(self, widget):
		## Quits the program.
		# Stop the player first to avoid tracebacks.
		self.stopPlayer()
		# Save the configuration to the file.
		self.cfg.save()
		gtk.main_quit()
	
	
	def videoWindowExpose(self, widget, event):
		# Pull the dimensions etc.
		x, y, w, h = event.area
		
		# Let the whole thing be drawn upon.
		widget.window.draw_drawable(widget.get_style().bg_gc[gtk.STATE_NORMAL],
		                            self.pixmap, x, y, x, y, w, h)
	
	
	def videoWindowConfigure(self, widget):
		# Get the windows allocation.
		x, y, w, h = widget.get_allocation()
		
		# Make a new pixmap (does this create a leak?)
		self.pixmap = gtk.gdk.Pixmap(widget.window, w, h)
		
		# Fill the whole thing with black so it looks nicer (better than white).
		self.pixmap.draw_rectangle(widget.get_style().black_gc, True, 0, 0, w, h)
		# Queue the drawing area.
		widget.queue_draw()
	
	
	def videoActivateFullScreen(self, widget=None):
		## This shows the full screen window for videos.
		# If it's not playing a video, or the fullscreen window is
		# already shown, don't continue.
		if (not self.player.playingVideo or self.fsWindowShown): return
		if (self.fsWindow):
			# If the window's already been created, just re-show it.
			self.fsWindow.show()
		else:
			# Otherwise, create it.
			windowname = 'videoFS'
			videoFSt = gtk.glade.XML(self.gladefile, windowname)
			dic = { "on_videoWindowFS_expose_event" : self.videoWindowExpose,
			        "on_videoFS_key_press_event" : self.windowKeyPressed,
			        "on_videoWindowFS_button_press_event" : self.videoWindowClicked }
			videoFSt.signal_autoconnect(dic)
			
			# Set the new window to fullscreen (the whole reason we called
			# this function).
			videoFSt.get_widget(windowname).fullscreen()
			# Get the drawing area for later use.
			self.fsVideoWin = videoFSt.get_widget("videoWindowFS")
			# Get the window so it can be hidden and shown with ease.
			self.fsWindow = videoFSt.get_widget(windowname)

		# Set a timer to set the video output to the fullscreen window
		# in 100ms, maybe I should fix this, but I don't know how FIXME:
		gobject.timeout_add(self.cfg.getInt("misc", "fspaintdelayms", 100), self.setImageSink)

		# Flag the fullscreen window as being shown.
		self.fsWindowShown = True


	
	def videoHideFullScreen(self):
		# Unflag the fullscreen window.
		self.fsWindowShown = False
		# Reset the image sink.
		self.setImageSink()
		# Hide the fullscreen window.
		self.fsWindow.hide()
	
	
	def toggleFullScreen(self, widget=None):
		# If the fullscreen window is shown, hide it, otherwise, show it.
		if (self.fsWindowShown):
			self.videoHideFullScreen()
		else:
			self.videoActivateFullScreen()
	
	
	def setImageSink(self, widget=None):
		## Sets the image sink to 'widget' or whichever it discovers.
		## For some reason it I pass the widgets from other functions
		## to here the program likes to crash.
		if (not widget):
			# If no widget was passed, discover which it should use.
			widget = self.fsVideoWin if (self.fsWindowShown) else self.movieWindow
		
		# Configure the video area.
		self.videoWindowConfigure(widget)
		
		# Set the image sink accordingly.
		self.player.setImgSink(widget)
		
		return False
	
	
	def videoWindowClicked(self, widget, event):
		# Get the even information.
		x, y, state = event.window.get_pointer()
		
		if (event.type == gtk.gdk._2BUTTON_PRESS and state & gtk.gdk.BUTTON1_MASK):
			# If the window was double clicked, fullsreen toggle.
			self.toggleFullScreen()
		elif(event.type == gtk.gdk.BUTTON_PRESS and state & gtk.gdk.BUTTON2_MASK):
			# If it was middle clicked, toggle play/pause.
			self.togglePlayPause()
		
	
	
	def windowKeyPressed(self, widget, event):
		## Doesn't work well with compiz, and I should probably make the
		#  bindings customisable (event.keyval for that probably).
		if (event.string == ' '):
			# Toggle Play/Pause on Spacebar.
			self.togglePlayPause()
		elif (event.string == 'f'):
			# Toggle fullscreen on 'f'.
			self.toggleFullScreen()

	
	def preparePlayer(self):
		## This prepares the player.
		# Create a new player.
		self.player = player.player()
		# Get the bus and connect the signals.
		bus = self.player.getBus()
		bus.connect('message', self.onPlayerMessage)
		bus.connect('sync-message::element', self.onPlayerSyncMessage)
		# Initialise the progress bar update timer.
		self.tmrProgress = None
	
	
	def onPlayerMessage(self, bus, message):
		mes = player.messages(message)
		if (mes.isEOS()):
			# At the end of a stream, stop the player.
			self.stopPlayer()
		elif (mes.isError()):
			# On an error, empty the currently playing file (also stops it).
			self.playFile(None)
	
	
	def onPlayerSyncMessage(self, bus, message):
		if (message.structure is None):
			return
		
		if (message.structure.get_name() == 'prepare-xwindow-id'):
			# If it's playing a video, set the video properties.
			self.player.prepareImgSink(bus, message)
			# Set the image sink to whichever viewer is active.
			self.setImageSink()
				
	
	def showOpenDialogue(self, widget=None):
		## Shows the open file dialogue.
		# Prepare the dialogue.
		dlg = dialogues.openFile(self.mainWindow, self.lastFolder)

		if (dlg.file):
			# If the response is OK, play the file.		
			self.playFile(dlg.file)
			# Also set the last folder.
			self.lastFolder = dlg.dir
	
	
	def openDroppedFile(self, widget, drag_context, x, y, selection_data, info, timestamp):
		## Opens a file after a drag and drop.
		# Split all the files that were input.
		uris = selection_data.data.strip().split()
		# Can only play one file at once, so use the first one.
		uri = uris[0]
		
		if (uri.startswith('file://')):
			# If it starts with file, remove it.
			file = urllib.url2pathname(uri[7:]).strip('\r\n\x00')
		
		# Actually play the file.
		self.playFile(file)
	
	
	def playFile(self, file):
		## Plays the file 'file'.
		# First, stop the player.
		self.stopPlayer()
		
		if (file == None): file = ""
		# Set the file, and the label.
		self.player.setURI("file://" + file)
		self.nowPlyLbl.set_label("" + file)
		if (os.path.exists(file)):
			# Start the player.
			self.startPlayer()
		elif (file != ""):
			# If none of the above, a bad filename was passed.
			print "Something's stuffed up, no such file: " + file
			
	
	def togglePlayPause(self, widget=None):
		## Toggles the player play/pause.
		
		if (not self.player.getURI()):
			# If there is no currently playing track, we should show the
			# open file dialogue.
			self.showOpenDialogue()
			return
		
		if (self.player.isPlaying()):
			# If the player is playing, pause the player.
			self.pausePlayer()
		else:
			# If it's already paused (or stopped with a file): play.
			self.startPlayer()
	
	
	def minuteTimer(self):
		## A timer that runs every minute while playing.
		# Disable XScreenSaver (if option is enabled).
		if (self.cfg.getBool("main", "disablexscreensaver", True) and self.player.playingVideo):
			os.system("xscreensaver-command -deactivate >&- 2>&-")
			os.system("xset s reset >&- 2>&-") # Does this do anything? I may have to test that.
			#if(int(os.system("xscreensaver-command -deactivate >&- 2>&-")) == 32512):
			#	self.cfg.set("main", "disablexscreensaver", False)
		
		return self.player.isPlaying()
	
	
	def secondTimer(self):
		# A function that's called once a second while playing.
		self.progressUpdate()
		
		# Causes it to go again if it's playing, but stop if it's not.
		return self.player.isPlaying()
		
	
	def progressUpdate(self):
		## Updates the progress bar.
		if (self.player.isStopped()):
			# If the player is stopped, played time and total should 
			# be 0, and the progress should be 0.
			pld = tot = 0
			self.progressBar.set_fraction(0)
		else:
			# Otherwise (playing or paused), get the track time data, set
			# the progress bar fraction.
			pld, tot = self.player.getTimesSec()
			if (tot != -1): self.progressBar.set_fraction(pld / tot)
		
		# Convert played & total time to integers
		p, t = int(pld), int(tot)
		# Add the data to the progress bar's text.
		text = ""
		text += "%d:%02d" % (p / 60, p % 60)
		if (tot != -1):
			text += " / "
			text += "%d:%02d" % (t / 60, t % 60)
		self.progressBar.set_text(text)
		
	
	def seekFromProgress(self, widget, event):
		## Seeks the file, from the progress bar.
		# If it's stopped, there's no point in seeking.
		if (self.player.isStopped()): return
		# Get the x position of the cursor.
		x, y, state = event.window.get_pointer()
		if (not (state & gtk.gdk.BUTTON1_MASK)): return
		# Get the width of the widget.
		maxX = widget.get_allocation().width
		# Seek to the location.
		self.player.seekFrac(float(x) / maxX)
		# Update the progress bar to reflect the change.
		self.progressUpdate()
		
	
	def changeVolume(self, adj):
		## Change the volume to that indicated by the volume bar.
		vol = adj.get_value()
		self.player.setVolume(vol)
		# Set the new volume on the configuration.
		self.cfg.set("main", "volume", vol)
	
	
	def startPlayer(self, widget=None):
		## Starts the player playing.
		# Create the timers.
		self.createPlayTimers()
		# Actually start the player.
		self.player.play()
		# Set the play/pause image to pause.
		self.setPlayPauseImage(1)
		
	def pausePlayer(self, widget=None):
		## Pauses the player.
		# Destroy the play timers.
		self.destroyPlayTimers()
		# Pause the player.
		self.player.pause()
		# Set the play/pause image to play.
		self.setPlayPauseImage(0)
	
	def stopPlayer(self, widget=None):
		## Stops the player.
		# Destroy the timers.
		self.destroyPlayTimers()
		# Stop the player.
		self.player.stop()
		# Set the play/pause image to play.
		self.setPlayPauseImage(0)
		# Update the progress bar.
		self.progressUpdate()
	
	
	def setPlayPauseImage(self, playing):
		## Changes the play/pause image according to the argument.
		# Set the size.
		size = gtk.ICON_SIZE_SMALL_TOOLBAR
		if (not playing):
			# If it's not playing, set the icon to play.
			img = gtk.image_new_from_stock('gtk-media-play', size)
		else:
			# If it is playing, set the icon to pause.
			img = gtk.image_new_from_stock('gtk-media-pause', size)
		
		# Actually set the icon.
		self.wTree.get_widget("btnPlayToggle").set_image(img)
	
	
	def createPlayTimers(self):
		# Create timers that go off every minute, and second.
		self.tmrSec = gobject.timeout_add(1000, self.secondTimer)
		self.tmrMin = gobject.timeout_add(60000, self.minuteTimer)
	
	def destroyPlayTimers(self):
		# Destroy the timers since nothing's happening.
		try:
			gobject.source_remove(self.tmrMin)
			gobject.source_remove(self.tmrSec)
		except:
			pass
		
	
	def showAboutDialogue(self, widget):
		dialogues.AboutDialogue(self.gladefile, whaawmpVersion)

	
	def __init__(self):
		## Initialises everything.
		# Option Parser
		parser = OptionParser()
		(options, args) = parser.parse_args()
		origDir = args[len(args)-1] # Directory from which whaawmp was called.
		# Open the settings.
		cfgdir = "%s%s.config%swhaawmp" % (os.getenv('HOME'), os.sep, os.sep)
		cfgfile = "config.ini"
		self.cfg = config.open_config(cfgdir, cfgfile)
		# Creates the window.
		windowname = "main"
		self.wTree = gtk.glade.XML(self.gladefile, windowname)
		
		dic = { "on_main_destroy" : self.quit,
		        "on_mnuiQuit_activate" : self.quit,
		        "on_mnuiOpen_activate" : self.showOpenDialogue,
		        "on_btnPlayToggle_clicked" : self.togglePlayPause,
		        "on_btnStop_clicked" : self.stopPlayer,
		        "on_pbarProgress_button_press_event" : self.seekFromProgress,
		        "on_pbarProgress_motion_notify_event" : self.seekFromProgress,
		        "on_vscVolume_value_changed" : self.changeVolume,
		        "on_mnuiFS_activate" : self.toggleFullScreen,
		        "on_videoWindow_expose_event" : self.videoWindowExpose,
		        "on_main_key_press_event" : self.windowKeyPressed,
		        "on_videoWindow_button_press_event" : self.videoWindowClicked,
		        "on_mnuiAbout_activate" : self.showAboutDialogue,
		        "on_main_drag_data_received" : self.openDroppedFile }
		self.wTree.signal_autoconnect(dic)
		
		# Get several items for access later.
		self.mainWindow = self.wTree.get_widget(windowname)
		self.progressBar = self.wTree.get_widget("pbarProgress")
		self.movieWindow = self.wTree.get_widget("videoWindow")
		self.nowPlyLbl = self.wTree.get_widget("lblNowPlaying")
		# Set the window to allow drops
		self.mainWindow.drag_dest_set(gtk.DEST_DEFAULT_ALL, [("text/uri-list", 0, 0)], gtk.gdk.ACTION_COPY)
		# Prepare the player for playing.
		self.preparePlayer()
		# Update the progress bar.
		self.progressUpdate()
		# Get the volume from the configuration.
		self.wTree.get_widget("vscVolume").get_adjustment().value = self.cfg.getFloat("main", "volume", 75)
		# Set up the default flags.
		self.fsWindowShown = False
		self.fsWindow = None
		# Play a file (if it was specified on the command line).
		if (len(args) > 1):
			filename = args[0]
			if (not (filename.startswith('/'))):
				filename = origDir + os.sep + filename
			
			self.playFile(filename)
		
		# Set the last folder to the directory from which the program was called.
		self.lastFolder = origDir
		# Configure the video area.
		self.videoWindowConfigure(self.movieWindow)
		
		return


main()
gtk.main()
