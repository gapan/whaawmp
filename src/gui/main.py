# -*- coding: utf-8 -*-

#  Whaaw! Media Player main window.
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

import sys, os, urllib
import pygtk
pygtk.require('2.0')
import gtk, gobject
gobject.threads_init()
import gtk.glade

from common import gstPlayer as player
from gui import dialogues
from gui.queue import queue
from common import lists, useful
from common import gstTools as playerTools
from common import mutagenTagger as tagger
from common.config import cfg

class mainWindow:
	def quit(self, widget=None, event=None):
		## Quits the program.
		# Stop the player first to avoid tracebacks.
		self.player.stop()
		# Save the configuration to the file.
		cfg.save()
		gtk.main_quit()
	
	
	def videoWindowExpose(self, widget, event):
		# Pull the dimensions etc.
		x, y, w, h = event.area
		
		# Let the whole thing be drawn upon.
		widget.window.draw_drawable(widget.get_style().bg_gc[gtk.STATE_NORMAL],
		                            self.pixmap, x, y, x, y, w, h)
		
		# If we're not playing, configure the player accordingly.
		if (not self.player.playingVideo()): self.videoWindowOnStop()
	
	
	def videoWindowConfigure(self, widget, event=None):
		# Get the windows allocation.
		x, y, w, h = widget.get_allocation()
		
		# Make a new pixmap (does this create a leak?)
		self.pixmap = gtk.gdk.Pixmap(widget.window, w, h)
		
		# Fill the whole thing with black so it looks nicer (better than white).
		self.pixmap.draw_rectangle(widget.get_style().black_gc, True, 0, 0, w, h)
		# Queue the drawing area.
		widget.queue_draw()
	
	
	def videoWindowMotion(self, widget, event):
		## Called when the cursor moves over a video window.
		# If the controls aren't already shown, show them.
		self.showControls()
		# Restart the idle timer.
		self.restartIdleTimer()
	
	
	def videoWindowLeave(self, widget, event):
		## If the mouse has left the window, destroy the idle timer
		## (So when fullscreen & mouse over controls, they don't disappear)
		self.removeIdleTimer()

	def videoWindowEnter(self, widget, event):
		## Restart the idle timer as the mouse has entered the widget.
		self.restartIdleTimer()	
	
	def restartIdleTimer(self):
		## Restarts the idle timer by removing it and creating it again.
		self.removeIdleTimer()
		self.createIdleTimer()
		
	def removeIdleTimer(self):
		try:
			# Stop the timer to hide the cursor.
			gobject.source_remove(self.idleTimer)
		except:
			pass
	
	def createIdleTimer(self):
		# Create the timer again, with the timeout reset.
		self.idleTimer = gobject.timeout_add(cfg.getInt("gui/mousehidetimeout"), self.hideControls)
	
	
	def showControls(self):
		## Shows the fullscreen controls (also the mouse):
		# Re show the cursor.
		self.setCursor(None, self.videoWindow)
		# Shows all the widgets that should be shown.
		if (not self.controlsShown):
			# If the controls aren't shown, show them.
			for x in lists.fsShowWMouse:
				self.wTree.get_widget(x).show()
			# Flag the controls as being shown.
			self.controlsShown = True
	
	
	def hideControls(self):
		## Hides the fullscreen controls (also the mouse).
		# We don't want anything hidden if no video is playing.
		if (not self.videoWindowShown()): return
		# Hide the cursor.
		self.hideCursor(self.videoWindow)
		if (self.fsActive()):
			# Only hide the controls if we're in fullscreen.
			# Hides all the widgets that should be hidden.
			for x in lists.fsShowWMouse:
				self.wTree.get_widget(x).hide()
			# Flag the controls as being hidden.
			self.controlsShown = False
	
	
	def hideCursor(self, widget):
		## Hides the cursor (Thanks to mirage for the code).
		# If there's no video playing, cancel it.
		if (not self.videoWindowShown()): return
		pix_data = useful.hiddenCursorPix
		colour = gtk.gdk.Color()
		pix = gtk.gdk.pixmap_create_from_data(None, pix_data, 1, 1, 1, colour, colour)
		invisible = gtk.gdk.Cursor(pix, pix, colour, colour, 0, 0)
		# Set the cursor to the one just created.
		self.setCursor(invisible, widget)
	
	def setCursor(self, mode, widget):
		## Sets a cursor to the one specified.
		widget.window.set_cursor(mode)
	
	
	def activateFullscreen(self, widget=None):
		## Activates fullscreen.
		# No use in doing fullscreen if no video is playing.
		if (not self.videoWindowShown()): return
		
		# Set the window to fullscreen.
		self.mainWindow.fullscreen()
	
	# Checks if we should allow Fullscreen functions (It's 1 if it's hidden).
	videoWindowShown = lambda self: self.videoWindow.get_allocation().height > 1

	
	def deactivateFullscreen(self):
		## Deactivates the fullscreen.
		# Hide all the widgets, before we unfullscreen.
		for x in lists.hiddenFSWidgets:
			self.wTree.get_widget(x).hide()
		# Unfullscreen the window when we're idle (stops weird dimensions).
		gobject.idle_add(self.mainWindow.unfullscreen)
	
	
	def toggleFullscreen(self, widget=None):
		# If the fullscreen window is shown, hide it, otherwise, show it.
		if (self.fsActive()):
			self.deactivateFullscreen()
		else:
			self.activateFullscreen()
	
	
	def setImageSink(self, widget=None):
		## Sets the image sink to 'widget' or whichever it discovers.
		if (not widget):
			# If no widget was passed, use the right one. (This is left from
			# when I had a separate fullscreen window, maybe it should be fixed?)
			widget = self.videoWindow
		
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
			self.toggleFullscreen()
		elif (event.type == gtk.gdk.BUTTON_PRESS and state & gtk.gdk.BUTTON2_MASK):
			# If it was middle clicked, toggle play/pause.
			self.togglePlayPause()

	
	def videoWindowScroll(self, widget, event):
		## Changes the volume on scroll up/down.
		if (event.direction == gtk.gdk.SCROLL_UP):
			self.increaseVolumeBy(cfg.getFloat('gui/volumescrollchange'))
		elif (event.direction == gtk.gdk.SCROLL_DOWN):
			self.increaseVolumeBy(0 - cfg.getFloat('gui/volumescrollchange'))
	
	
	def increaseVolumeBy(self, change):
		## Increases the volume by the amount given.
		val = self.volAdj.value + change
		# Make sure the new value is withing the bounds (0 <= val <= 100)
		val = useful.toRange(val, 0, 100)
		# Adjust the volume.
		self.volAdj.value = val
	
	
	def windowKeyPressed(self, widget, event):
		## I should probably make the bindings customisable (event.keyval
		# for that probably).
		if (event.string == ' '):
			# Toggle Play/Pause on Spacebar.
			self.togglePlayPause()
		elif (event.string == 'f'):
			# Toggle fullscreen on 'f'.
			self.toggleFullscreen()
		elif (event.string == 'n'):
			# Skip to the next track on 'n'.
			self.playNext()

	
	def preparePlayer(self):
		## This prepares the player.
		# Create a new player.
		self.player = player.player()
		# Get the bus and connect the signals.
		bus = self.player.getBus()
		bus.connect('message', self.onPlayerMessage)
		bus.connect('sync-message::element', self.onPlayerSyncMessage)
		# Sets the sinks to that in the config (unless one was specified at launch).
		asink = cfg.getStr("audio/audiosink") if (not self.options.audiosink) else self.options.audiosink
		self.player.setAudioSink(None if (asink == "default") else asink)
		vsink = cfg.getStr("video/videosink") if (not self.options.videosink) else self.options.videosink
		self.player.setVideoSink(playerTools.vsinkDef() if (vsink == "default") else vsink)
	
	
	def onPlayerMessage(self, bus, message):
		t = playerTools.messageType(message)
		if (t == 'eos'):
			# At the end of a stream, play next item from queue.
			self.playNext()
		elif (t == 'error'):
			# On an error, empty the currently playing file (also stops it).
			self.playFile(None)
			# Show an error about the failure.
			msg = message.parse_error()
			dialogues.ErrorMsgBox(self.mainWindow, str(msg[0]) + '\n\n' + str(msg[1]), _('Error!'))
		elif (t == 'state_changed' and message.src == self.player.player):
			self.onPlayerStateChange(message)
	
	
	def onPlayerStateChange(self, message):
		# On a state change.
		msg = message.parse_state_changed()
		if (playerTools.isNull2ReadyMsg(msg)):
			# Enable the visualisation if requested.
			if (cfg.getBool('gui/enablevisualisation')):
				self.player.enableVisualisation()
			else:
				self.player.disableVisualisation()
		
		elif (playerTools.isStop2PauseMsg(msg)):
			# The player has gone from stopped to paused.
			# Get the array of audio tracks.
			self.audioTracks = playerTools.getAudioLangArray(self.player)
			# Only enable the audio track menu item if there's more than one audio track.
			self.wTree.get_widget('mnuiAudioTrack').set_sensitive(len(self.audioTracks) > 1)
			# Enable the visualisation if requested.
			if (cfg.getBool('gui/enablevisualisation')):
				self.player.enableVisualisation()
			else:
				self.player.disableVisualisation()
			# Set the title accordingly.
			self.setPlayingTitle(self.player.getURI())
		
		elif (playerTools.isPlayMsg(msg)):
			# The player has just started.
			# Set the play/pause image to pause.
			self.playPauseChange(True)
			# Create the timers.
			self.createPlayTimers()
			
		elif (playerTools.isPlay2PauseMsg(msg)):
			# It's just been paused or stopped.
			self.playPauseChange(False)
			# Destroy the play timers.
			self.destroyPlayTimers()
			# Update the progress bar.
			self.progressUpdate()
			
		elif (playerTools.isStopMsg(msg)):
			if ((not self.player.isPlaying()) and self.wTree.get_widget("mnuiQuitOnStop").get_active()): self.quit()
			# Draw the background image.
			self.videoWindowOnStop()
			# Deactivate fullscreen.
			if (self.fsActive()): self.deactivateFullscreen()
			# Reset the progress bar.
			self.progressUpdate()
			# Clear the title.
			self.setPlayingTitle(None)
	
	
	def onPlayerSyncMessage(self, bus, message):
		if (message.structure is None):
			return
		
		if (message.structure.get_name() == 'prepare-xwindow-id'):
			# If it's playing a video, set the video properties.
			# First, show the video window.
			self.showVideoWindow()
			# Get the properties of the video.(Brightness etc)
			far = cfg.getBool("video/force-aspect-ratio")
			b = cfg.getInt("video/brightness")
			c = cfg.getInt("video/contrast")
			h = cfg.getInt("video/hue")
			s = cfg.getInt("video/saturation")
			self.player.prepareImgSink(bus, message, far, b, c, h, s)
			# Set the image sink to whichever viewer is active.
			# (idle_add to stop crashes when the video window wasn't shown yet)
			gobject.idle_add(self.setImageSink)
				
	
	def openDroppedFiles(self, widget, context, x, y, selection_data, info, time):
		## Opens a file after a drag and drop.
		# Split all the files that were input.
		uris = selection_data.data.strip().split()
		# Clear the current queue.
		queue.clear()
		# Add all the items to the queue.
		for x in uris:
			uri = urllib.url2pathname(x)
			queue.append(uri)
		
		# Play the first file by calling the next function.
		self.playNext()
		# Finish the drag.
		context.finish(True, False, time)
	
	def playNext(self, widget=None):
		## Plays the next file in the queue (if it exists).
		self.playFile(queue.getNextTrackRemove())
	
	def playFile(self, file):
		## Plays the file 'file' (Could also be a URI).
		# First, stop the player.
		self.player.stop()
		# Set the audio track to 0
		self.player.setAudioTrack(0)
		
		if (file == None):
			# If no file is to be played, set the URI to None, and the file to ""
			file = ""
			self.player.setURI(file)
		# Set the now playing label to the file to be played.
		self.nowPlyLbl.set_label("" + file)
		if (os.path.exists(file) or '://' in file):
			# If it's not already a uri, make it one.
			if ('://' not in file): file = 'file://' + file
			# Set the URI to the file's one.
			self.player.setURI(file)
			# Add the file to recently opened files.
			self.addToRecent(file)
			# Start the player.
			self.player.play()
		elif (file != ""):
			# If none of the above, a bad filename was passed.
			print _("Something's stuffed up, no such file: %s") % (file)
			self.playFile(None)
	
	
	def setPlayingTitle(self, uri):
		if (uri):
			# If the URI passed isn't 'None'.
			# If we don't want to set it, return.
			if (not cfg.getBool('gui/fileastitle')): return
			# Set the title name.
			titlename = tagger.getDispTitle(uri) + ' - ' + useful.lName
		else:
			# Otherwise set the title to just the normal name.
			titlename = useful.lName
		# Actually set it!
		self.mainWindow.set_title(titlename)


	def addToRecent(self, uri):
		## Adds a certain URI to the recent files list.
		gtk.recent_manager_get_default().add_item(uri)
		
	
	def playDVD(self, title=None):
		## Plays a DVD
		# Start the player playing the DVD.
		self.playFile('dvd://%s' % (title if (title != None) else ""))
			
	
	def togglePlayPause(self, widget=None):
		## Toggles the player play/pause.
		
		if (not self.player.getURI()):
			# If there is no currently playing track.
			# Check the queue.
			if (queue.length()):
				self.playNext()
			else:
				# Otherwise show the open file dialogue.
				self.showOpenDialogue()
			return
		
		if (self.player.isPlaying()):
			# If the player is playing, pause the player.
			self.player.pause()
		else:
			# If it's already paused (or stopped with a file): play.
			self.player.play()
	
	
	def minuteTimer(self):
		## A timer that runs every minute while playing.
		# Disable ScreenSaver (if option is enabled).
		if (cfg.getBool("misc/disablescreensaver") and self.videoWindowShown()):
			# For all the commands in the disable screensaver config option, run them.
			for x in cfg.getStr("misc/disablescrcmd").split(','):
				useful.hiddenExec(x)
		
		return self.player.isPlaying()
	
	
	def secondTimer(self):
		# A function that's called once a second while playing.
		if (not self.seeking): self.progressUpdate()
		
		# Causes it to go again if it's playing, but stop if it's not.
		return self.player.isPlaying()
		
	
	def progressUpdate(self, pld=None, tot=None):
		## Updates the progress bar.
		if (self.player.isStopped()):
			# If the player is stopped, played time and total should 
			# be 0, and the progress should be 0.
			pld = tot = 0
			self.progressBar.set_fraction(0)
		else:
			# Otherwise (playing or paused), get the track time data, set
			# the progress bar fraction.
			if (pld == None or tot == None): pld, tot = self.player.getTimesSec()
			self.progressBar.set_fraction(pld / tot if (tot > 0) else 0)
		
		# Convert played & total time to integers
		p, t = int(pld), int(tot)
		# Add the data to the progress bar's text.
		text = ""
		text += useful.secToStr(p)
		if (tot > 0):
			text += " / "
			text += useful.secToStr(t - (cfg.getBool('gui/showtimeremaining') * p))
		self.progressBar.set_text(text)
	
	
	def onMainStateEvent(self, widget, event):
		## Acts when a state event occurs on the main window.
		fs = event.new_window_state & gtk.gdk.WINDOW_STATE_FULLSCREEN
		if (fs):
			# Hide all the widgets other than the video window.
			for x in lists.hiddenFSWidgets:
				self.wTree.get_widget(x).hide()
			
			# Flag the the controls as not being shown.
			self.controlsShown = False
		else:
			# Re-show all the widgets that aren't meant to be hidden.
			for x in lists.hiddenFSWidgets:
				if (x not in lists.hiddenNormalWidgets): self.wTree.get_widget(x).show()
			# Flag the controls as being shown.
			self.controlsShown = True
		

	def showVideoWindow(self):
		## Shows the video window.
		# Allow fullscreen.
		self.wTree.get_widget('mnuiFS').set_sensitive(True)
		# Show the video window.
		self.videoWindow.show()
	
	def hideVideoWindow(self, force=False):
		## Hides the video window.
		if (not self.fsActive() or force):
			# Disable fullscreen activation.
			self.wTree.get_widget('mnuiFS').set_sensitive(False)
			# Hide the video window.
			self.videoWindow.hide()
			# Make the height of the window as small as possible.
			w = self.mainWindow.get_size()[0]
			self.mainWindow.resize(w, 1)
		
	
	def progressBarClick(self, widget, event):
		## The progress bar has been clicked.
		x, y, state = event.window.get_pointer()
		if (state & gtk.gdk.BUTTON1_MASK and not self.player.isStopped() and self.player.getDuration()):
			# If it's button 1, it's not stopped and the duration exists: start seeking.
			self.seeking = True
			self.progressBarMotion(widget, event)
		else:
			# Otherwise do what would happen if the video window was clicked.
			self.videoWindowClicked(widget, event)
	
	
	def seekEnd(self, widget, event):
		## Sets that seeking has ended, and seeks to the position.
		if (self.seeking):
			self.seekFromProgress(widget, event)
			# Flag that seeking has stopped.
			self.seeking = False
	
	
	def seekFromProgress(self, widget, event):
		x, y, state = event.window.get_pointer()
		# Get the width & height of the bar.
		alloc = widget.get_allocation()
		maxX = alloc.width
		maxY = alloc.height
		# Seek if cursor is still vertically over the bar.
		if (y >= 0 and y <= maxY): self.player.seekFrac(float(x) / maxX)
		# Update the progress bar to reflect the change.
		self.progressUpdate()
		
		
	def progressBarMotion(self, widget, event):
		## when the mouse moves over the progress bar.
		# If we're not seeking, cancel.
		if (not self.seeking): return
		# Check if the mouse button is still down, just in case we missed it.
		x, y, state = event.window.get_pointer()
		if (not state & gtk.gdk.BUTTON1_MASK): self.seekEnd(widget, event)
		if (cfg.getBool("gui/instantseek")):
			# If instantaneous seek is set, seek!
			self.seekFromProgress(widget, event)
			return
		
		# Get the mouse co-ordinates, the width of the bar and the file duration.
		x, y = event.get_coords()
		maxX = widget.get_allocation().width
		dur = self.player.getDurationSec()
		# Convert the information to a fraction, and make sure 0 <= frac <= 1
		frac = useful.toRange(float(x) / maxX, 0, 1)
		
		# Set the progress bar to the new data.
		self.progressUpdate((frac * dur), dur)
		
	
	def volumeButtonToggled(self, widget):
		## Toggles Mute
		self.player.setVolume(self.volAdj.value if (widget.get_active()) else 0)
		# Save the mutedness in the config.
		cfg.set("audio/mute", not widget.get_active())
		
	def changeVolume(self, widget):
		## Change the volume to that indicated by the volume bar.
		vol = widget.get_value()
		self.player.setVolume(vol if (not cfg.getBool("audio/mute")) else 0)
		# Set the new volume on the configuration.
		cfg.set("audio/volume", vol)
	
	
	def playPauseChange(self, playing):
		## Changes the play/pause image according to the argument.
		# Set the size.
		size = cfg.getInt("gui/iconsize")
		# Set the icon accordingly (Not playing -> Pause button, otherwise, play.)
		img = gtk.image_new_from_stock('gtk-media-play' if (not playing) else 'gtk-media-pause', size)
		
		btn = self.wTree.get_widget("btnPlayToggle")
		# Actually set the icon.
		btn.set_image(img)
		# Also set the tooltip.
		self.tooltips.set_tip(btn, _('Pause') if (playing) else _('Play'))
		# Set the stop button image too.
		self.wTree.get_widget("btnStop").set_image(gtk.image_new_from_stock('gtk-media-stop', size))
		# And the next one.
		self.wTree.get_widget("btnNext").set_image(gtk.image_new_from_stock('gtk-media-next', size))
		
	
	
	def createPlayTimers(self):
		# Destroy the timers first to avoid about 20 of them.
		self.destroyPlayTimers()
		# Create timers that go off every minute, and second.
		self.tmrSec = useful.addTimer(1, self.secondTimer)
		self.tmrMin = useful.addTimer(60, self.minuteTimer)
	
	def destroyPlayTimers(self):
		# Destroy the timers since nothing's happening.
		try:
			gobject.source_remove(self.tmrMin)
			gobject.source_remove(self.tmrSec)
		except:
			pass
	
	
	def videoWindowOnStop(self, force=False):
		## Called when the player stops, acts on the video window.
		# If we're still playing a video, we shouldn't act.
		if (self.player.playingVideo()): return
		if (cfg.getBool("gui/hidevideowindow")):
			# If the video window should be hidden, hide it, otherwise, draw the picture.
			self.hideVideoWindow(force)
		else:
			self.showVideoWindow()
			self.drawvideoWindowImage()
	
	
	def drawvideoWindowImage(self):
		## Draws the background image.
		# Get the width & height of the videoWindow.
		alloc = self.videoWindow.get_allocation()
		w = alloc.width
		h = alloc.height
		if (w < h):
			# It's wider than it is high, use the width as the size
			# & find where the image should start.
			size = w
			x1 = 0
			y1 = (h - w) / 2
		else:
			# Do the opposite.
			size = h
			x1 = (w - h) / 2
			y1 = 0
		
		# Get the image's path, chuck it into a pixbuf, then draw it!
		image = os.path.join(useful.dataDir, 'images', 'whaawmpL.svg')
		bgPixbuf = gtk.gdk.pixbuf_new_from_file_at_size(image, size, size)
		self.videoWindow.window.draw_pixbuf(self.videoWindow.get_style().black_gc,bgPixbuf.scale_simple(size, size, gtk.gdk.INTERP_NEAREST), 0, 0, x1, y1)

	
	def fsActive(self):
		## Returns True if fullscreen is active.
		return self.mainWindow.window.get_state() & gtk.gdk.WINDOW_STATE_FULLSCREEN
		
	
	def showOpenDialogue(self, widget=None):
		## Shows the open file dialogue.
		# Prepare the dialogue.
		dlg = dialogues.OpenFile(self.mainWindow, self.lastFolder)

		if (dlg.file):
			# If the response is OK, play the file.		
			self.playFile(dlg.file)
			# Also set the last folder, (if it exists).
			if (dlg.dir): self.lastFolder = dlg.dir
	
	
	def showAboutDialogue(self, widget):
		dialogues.AboutDialogue(self.mainWindow)
	
	
	def showPreferencesDialogue(self, widget):
		dialogues.PreferencesDialogue(self, self.mainWindow)
	
	def showPlayDVDDialogue(self, widget):
		# Create the dialogue.
		dlg = dialogues.PlayDVD(self.mainWindow)
		if (dlg.res):
			self.playDVD(dlg.Title)
	
	def showOpenURIDialogue(self, widget):
		# Create and get the dialogue.
		dlg = dialogues.OpenURI(self.mainWindow)
		if (dlg.res):
			# If something was input, play it.
			self.playFile(dlg.URI)
	
	def showAudioTracksDialogue(self, widget):
		# Show the audio track selection dialogue (hopefully will handle subtitles too soon.
		dialogues.SelectAudioTrack(self.mainWindow, self.audioTracks, self.player)
	
	def toggleQueueWindow(self, widget):
		# Toggle the queue window according to what the menu item is set to.
		queue.toggle(widget.get_active())
	
	def connectLinkHooks(self):
		## Make hooks for opening URLs and e-mails.
		if (useful.checkLinkHandler):
			gtk.about_dialog_set_email_hook(self.URLorMailOpen, 'mail')
			gtk.about_dialog_set_url_hook(self.URLorMailOpen, 'url')
		else:
			# xdg-open doesn't exist.
			print _("%s not found, links & e-mail addresses will not be clickable" % useful.linkHandler)
	
	def URLorMailOpen(self, dialog, link, type):
		# Transfers the call to the useful call.
		useful.URLorMailOpen(link, type)
	
	def openBugReporter(self, widget):
		## Opens the bugs webpage.
		link = "http://gna.org/bugs/?func=additem&group=whaawmp"
		if (useful.checkLinkHandler):
			useful.URLorMailOpen(link)
		else:
			dialogues.ErrorMsgBox(self.mainWindow, _("Could not execute browser command (via %s).\nPlease manually visit %s to report the problem" % (useful.linkHandler, link)))
	
	# Just a transfer call as player.stop takes only 1 argument.
	stopPlayer = lambda self, widget: self.player.stop()
	
	
	def __init__(self, main, options, args):
		# Set the last folder to the directory from which the program was called.
		self.options = options
		self.lastFolder = useful.origDir
		# Set the application's name (for about dialogue etc).
		## TODO, remove this if when glib 2.14 is more widespread.
		if (gobject.glib_version >= (2,14)):
			gobject.set_application_name(useful.lName)
		
		# Create & prepare the player for playing.
		self.preparePlayer()
		
		windowname = "main"
		self.wTree = gtk.glade.XML(useful.gladefile, windowname, useful.sName)
		
		dic = { "on_main_delete_event" : self.quit,
		        "on_mnuiQuit_activate" : self.quit,
		        "on_mnuiOpen_activate" : self.showOpenDialogue,
		        "on_mnuiOpenURI_activate" : self.showOpenURIDialogue,
		        "on_btnPlayToggle_clicked" : self.togglePlayPause,
		        "on_btnStop_clicked" : self.stopPlayer,
		        "on_btnNext_clicked" : self.playNext,
		        "on_pbarProgress_button_press_event" : self.progressBarClick,
		        "on_pbarProgress_button_release_event" : self.seekEnd,
		        "on_pbarProgress_motion_notify_event" : self.progressBarMotion,
		        "on_chkVol_toggled" : self.volumeButtonToggled,
		        "on_hscVolume_value_changed" : self.changeVolume,
		        "on_mnuiFS_activate" : self.toggleFullscreen,
		        "on_btnLeaveFullscreen_clicked" : self.toggleFullscreen,
		        "on_videoWindow_expose_event" : self.videoWindowExpose,
		        "on_videoWindow_configure_event" : self.videoWindowConfigure,
		        "on_main_key_press_event" : self.windowKeyPressed,
		        "on_videoWindow_button_press_event" : self.videoWindowClicked,
		        "on_videoWindow_scroll_event" : self.videoWindowScroll,
		        "on_hscVolume_scroll_event" : self.videoWindowScroll,
		        "on_mnuiAbout_activate" : self.showAboutDialogue,
		        "on_main_drag_data_received" : self.openDroppedFiles,
		        "on_videoWindow_motion_notify_event" : self.videoWindowMotion,
		        "on_videoWindow_leave_notify_event" : self.videoWindowLeave,
		        "on_videoWindow_enter_notify_event" : self.videoWindowEnter,
		        "on_mnuiPreferences_activate" : self.showPreferencesDialogue,
		        "on_mnuiPlayDVD_activate" : self.showPlayDVDDialogue,
		        "on_mnuiAudioTrack_activate" : self.showAudioTracksDialogue,
		        "on_mnuiReportBug_activate" : self.openBugReporter,
		        "on_main_window_state_event" : self.onMainStateEvent,
		        "on_mnuiQueue_toggled" : self.toggleQueueWindow }
		self.wTree.signal_autoconnect(dic)
		
		# Get several items for access later.
		self.mainWindow = self.wTree.get_widget(windowname)
		self.progressBar = self.wTree.get_widget("pbarProgress")
		self.videoWindow = self.wTree.get_widget("videoWindow")
		self.nowPlyLbl = self.wTree.get_widget("lblNowPlaying")
		self.volAdj = self.wTree.get_widget("hscVolume").get_adjustment()
		self.hboxVideo = self.wTree.get_widget("hboxVideo")
		queue.mnuiWidget = self.wTree.get_widget("mnuiQueue")
		# Set the icon.
		self.mainWindow.set_icon_from_file(os.path.join(useful.dataDir, 'images', 'whaawmp.svg'))
		# Create a tooltips instance for use in the code.
		self.tooltips = gtk.Tooltips()
		# Set the window to allow drops
		self.mainWindow.drag_dest_set(gtk.DEST_DEFAULT_ALL, [("text/uri-list", 0, 0)], gtk.gdk.ACTION_COPY)
		# Update the progress bar.
		self.progressUpdate()
		# Get the volume from the configuration.
		self.wTree.get_widget("chkVol").set_active(not (cfg.getBool("audio/mute") or (options.mute)))
		self.volAdj.value = cfg.getFloat("audio/volume") if (options.volume == None) else float(options.volume)
		# Set the quit on stop checkbox.
		self.wTree.get_widget("mnuiQuitOnStop").set_active(options.quitOnEnd)
		# Set up the default flags.
		self.controlsShown = True
		self.seeking = False
		# Call the function to change the play/pause image.
		self.playPauseChange(False)
		# Show the next button if enabled.
		if (cfg.getBool("gui/shownextbutton")): self.wTree.get_widget("btnNext").show()
		# Show the window.
		self.mainWindow.show()
		# Play a file (if it was specified on the command line).
		if (len(args) > 0):
			for x in args:
				# For all the files, add them to the queue.
				queue.append(x if ('://' in x) else os.path.abspath(x))
			# Then play the next track.
			self.playNext()
		else:
			self.videoWindowOnStop(True)
		
		if (options.fullscreen):
			# If the fullscreen option was passed, start fullscreen.
			self.activateFullscreen()
		
		# Connect the hooks.
		self.connectLinkHooks()
		
		# Enter the GTK main loop.
		gtk.main()
