#!/usr/bin/env python

#  A player module for gstreamer.
#  Copyright (C) 2007, Jeff Bailes <thepizzaking@gmail.com>
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

import pygst
pygst.require('0.10')
import gst
from common import lists, useful


class player:
	colourSettings = False
	aspectSettings = False
	
	def play(self):
		# Starts the player playing.
		self.player.set_state(gst.STATE_PLAYING)
	
	def pause(self):
		# Pauses the player.
		self.player.set_state(gst.STATE_PAUSED)
	
	def stop(self):
		# Stops the player.
		self.player.set_state(gst.STATE_READY)
	

	def playingVideo(self):
		# If current-video is -1, a video is not playing.
		return (self.player.get_property('current-video') != -1 or self.player.get_property('vis-plugin') != None)
	
	# Returns true if the player is playing, false if not.
	isPlaying = lambda self: self.getState() == gst.STATE_PLAYING
	# Returns true if the player is stopped, false if not.
	isStopped = lambda self: (self.getState() in [ gst.STATE_NULL, gst.STATE_READY ])
	# Returns true if the player is paused, false if not.
	isPaused = lambda self: self.getState() == gst.STATE_PAUSED
	
	# Returns the bus of the player.
	getBus = lambda self: self.player.get_bus()
	# Gets the current audio track.
	getAudioTrack = lambda self: self.player.get_property('current-audio')
	# Returns the state of the player.
	getState = lambda self: self.player.get_state()[1]
	# Returns the current URI.
	getURI = lambda self: self.player.get_property('uri')
	# Returns an array of stream information.
	getStreamsInfo = lambda self: self.player.get_property('stream-info-value-array')
	
	# Returns the times, played seconds and duration.
	getTimesSec = lambda self: (self.getPlayedSec(), self.getDurationSec())
	# Returns the played seconds.
	getPlayedSec = lambda self: useful.nsTos(self.getPlayed())
	# Returns the total duration seconds.
	getDurationSec = lambda self: useful.nsTos(self.getDuration())
	# Returns the played time (in nanoseconds).
	getPlayed = lambda self: self.player.query_position(gst.FORMAT_TIME)[0]
	
	def getDuration(self):
		# Returns the duration (nanoseconds).
		try:
			return self.player.query_duration(gst.FORMAT_TIME)[0]
		except:
			return 0
	
	
	def seekFrac(self, frac):
		# Seek from a fraction.
		dur = self.getDuration()
		# getDuration returns 0 on error.
		if (dur != 0):
			print self.getDuration() * frac
			self.seek(int(self.getDuration() * frac))
	
	def seek(self, loc):
		## Seeks to a set location in the track.
		# Seek to the requested position.
		#  | gst.SEEK_FLAG_ACCURATE removed from 3rd field (did removing fix lockups?)
		self.player.seek(1.0, gst.FORMAT_TIME,
		    gst.SEEK_FLAG_FLUSH,
		    gst.SEEK_TYPE_SET, loc,
		    gst.SEEK_TYPE_NONE, 0)
	
	
	def setURI(self, uri):
		# Sets the player's uri to the one specified.
		self.player.set_property('uri', uri)
	
	
	def prepareImgSink(self, bus, message, far=True, b=0, c=0, h=0, s=0):
		# Sets the image sink.
		self.imagesink = message.src
		# Sets force aspect ratio, brightness etc according to options passed.
		self.setForceAspectRatio(far)
		self.setBrightness(b)
		self.setContrast(c)
		self.setHue(h)
		self.setSaturation(s)
	
	
	def setImgSink(self, widget):
		## Sets the video output to the desired widget.
		self.imagesink.set_xwindow_id(widget.window.xid)
	
	def setForceAspectRatio(self, val):
		## Toggles force aspect ratio on or off.
		if (self.aspectSettings):
			self.imagesink.set_property('force-aspect-ratio', val)
	
	def setBrightness(self, val):
		## Sets the brightness of the video.
		if (self.colourSettings):
			self.imagesink.set_property('brightness', val)
	
	def setContrast(self, val):
		## Sets the contrast of the video.
		if (self.colourSettings):
			self.imagesink.set_property('contrast', val)
	
	def setHue(self, val):
		## Sets the hue of the video.
		if (self.colourSettings):
			self.imagesink.set_property('hue', val)
	
	def setSaturation(self, val):
		## Sets the saturation of the video.
		if (self.colourSettings):
			self.imagesink.set_property('saturation', val)
	
	
	def setAudioSink(self, sinkName):
		## Sets the player's audio sink.
		# If a name was passed, create the element, otherwise pass None
		sink = gst.element_factory_make(sinkName, 'audio-sink') if (sinkName) else None
		# Set the player's sink accordingly.
		self.player.set_property('audio-sink', sink)
	
	def setVideoSink(self, sinkName):
		## Sets the player's video sink.
		# If a name was passed, create the element, otherwise pass None
		sink = gst.element_factory_make(sinkName, 'video-sink')
		# Set the player's sink accordingly.
		self.player.set_property('video-sink', sink)
		# Flag the colour settings and aspect settings accordingly.
		self.colourSettings = (sinkName in lists.vsinkColour)
		self.aspectSettings = (sinkName in lists.vsinkAspect)
	
	
	def enableVisualisation(self):
		# Enable the visualisaion.
		try:
			self.player.set_property('vis-plugin', self.visPlugin)
		except:
			self.visPlugin = gst.element_factory_make('goom')
			self.player.set_property('vis-plugin', gst.element_factory_make('goom'))
	
	def disableVisualisation(self):
		# Diable the visualisaion.
		self.player.set_property('vis-plugin', None)
	
	
	def setVolume(self, vol):
		## Sets the volume to the requested percentage.
		self.player.set_property('volume', vol / 100)
	
	
	def setAudioTrack(self, track):
		## Sets the audio track to play.
		self.player.set_property('current-audio', track)
	
	
	def setSubtitleTrack(self, track):
		## Sets the subtitle track to play.
		self.player.set_property('current-text', track)
	
	
	def __init__(self):
		## Creates and prepares a player.
		# Create the player.
		self.player = gst.element_factory_make("playbin", "player")
		
		# Make the program emit signals.
		bus = self.getBus()
		bus.add_signal_watch()
		bus.enable_sync_message_emission()
