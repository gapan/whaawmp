# -*- coding: utf-8 -*-

#  DBus Backend
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

from common import useful

try:
	import dbus
	import dbus.service
	from dbus.mainloop.glib import DBusGMainLoop
	DBusGMainLoop(set_as_default=True)
	bus = dbus.SessionBus()
	avail = True	
except ImportError:
	print _("Dbus import failed, dbus features will be unavailable")
	# Dummy D-Bus library (From exaile)
	class _Connection:
		get_object = lambda *a: object()
	class _Interface:
		__init__ = lambda *a: None
		ListNames = lambda *a: []
	class Dummy: pass
	dbus = Dummy()
	dbus.Interface = _Interface
	dbus.service = Dummy()
	dbus.service.method = lambda *a: lambda f: f
	dbus.service.Object = object
	dbus.SessionBus = _Connection
	avail = False


class IntObject(dbus.service.Object):
	from common.gstPlayer import player
	from gui.queue import queue
	
	def __init__(self, mainWindow):
		# Initialises the bus so it can receive signals & handle them.
		name = dbus.service.BusName("org.gna.whaawmp", bus)
		dbus.service.Object.__init__(self, name, "/IntObject")
		self.main = mainWindow
	
	@dbus.service.method("org.gna.whaawmp", "s")
	def playFile(self, file):
		# Plays a file (well, enqueues it).
		self.queue.append(file)
		if (not self.player.getURI()): self.main.playNext()
	
	@dbus.service.method("org.gna.whaawmp", "", "b")
	def togglePlayPause(self):
		# Toggles the player to play/pause.
		return self.player.togglePlayPause()
	
	@dbus.service.method("org.gna.whaawmp", "", "b")
	def play(self):
		# Starts the player playing.
		return self.player.play()
	
	@dbus.service.method("org.gna.whaawmp", "", "b")
	def pause(self):
		# Pauses the player.
		return self.player.pause()

	@dbus.service.method("org.gna.whaawmp")
	def stop(self):
		# Stops the player.
		self.player.stop()

	@dbus.service.method("org.gna.whaawmp")
	def next(self):
		# Skips to the next track.
		self.main.playNext()

	@dbus.service.method("org.gna.whaawmp")
	def prev(self):
		# Restarts the current track.
		self.main.restartTrack()


class initBus:
	quitAfter = False
	
	def __init__(self, options, args):
		if (not avail): return
		
		try:
			# Try and connect to a previous whaawmp process.
			self.prepareIface()
		except dbus.exceptions.DBusException:
			# If that fails, whaawmp is not running, so just return and start
			# normally.
			return
		
		# If it gets to here, whaawmp is already running.
		print _("%s is already running." % useful.lName)
		
		for x in args:
			# Play all the files passed.
			self.iface.playFile(x)
			self.quitAfter = True
		
		if options.togglePlayPause:
			# Toggle play/pause.
			if (not self.iface.togglePlayPause()):
				print _("Toggle of Play/Pause failed, no file is currently open.")
			self.quitAfter = True
		
		if options.play:
			# Start playing.
			if (not self.iface.play()):
				print _("Play failed, no file is currently open.")
			self.quitAfter = True
		
		if options.pause:
			# Pause the player.
			if (not self.iface.pause()):
				print _("Pause failed, not file is currently open.")
			self.quitAfter = True
		
		if options.stop:
			# Stops the player.
			self.iface.stop()
			self.quitAfter = True
		
		if options.next:
			# Skip to the next track.
			self.iface.next()
			self.quitAfter = True
		
		if options.prev:
			# Restart current playing stream.
			self.iface.prev()
			self.quitAfter = True

			
	def prepareIface(self):
		# Try to connect to a previously running whaawmp process, this *will*
		# throw an exception if whaawmp is not running.
		ro = bus.get_object("org.gna.whaawmp", "/IntObject")
		self.iface = dbus.Interface(ro, "org.gna.whaawmp")
