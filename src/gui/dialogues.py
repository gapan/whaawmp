#!/usr/bin/env python

# Other Dialogues
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

import pygtk
pygtk.require('2.0')
import gtk, gtk.glade

class AboutDialogue:
	def __init__(self, gladefile, version):
		## Shows the about dialogue.
		windowname = 'AboutDlg'
		tree = gtk.glade.XML(gladefile, windowname)
		
		dlg = tree.get_widget(windowname)
		# Sets the correct version.
		dlg.set_version(version)
		
		# Run the destroy the dialogue.
		dlg.run()
		dlg.destroy()


class OpenFile:
	def __init__(self, parent, loc):
		## Does an open dialogue, puts the directory into dir and the file
		## in to file.
		# Create the dialogue.
		self.dlg = gtk.FileChooserDialog(("Choose a file"), parent,
		                  buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
		                             gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		
		# Set the current folder to the one passed.
		self.dlg.set_current_folder(loc)
		
		# Run the dialogue, then hide it.
		res = self.dlg.run()
		self.dlg.hide()
		
		# Save the current folder.
		self.dir = self.dlg.get_current_folder()
		self.file = self.dlg.get_filename() if (res == gtk.RESPONSE_OK) else None
		
		# Destroy the dialogue.
		self.dlg.destroy()


class PreferencesDialogue:
	def __init__(self, main, parent):
		## Shows the preferences dialogue.
		# Sets some variables for easier access.
		self.cfg = main.cfg
		self.player = main.player
		
		# Then create the dialogue and connect the signals.
		windowname = 'PreferencesDlg'
		self.wTree = gtk.glade.XML(main.gladefile, windowname)
		
		dic = { "on_PreferencesDlg_delete_event" : self.closeWindow,
		        "on_checkbox_toggled" : self.checkboxToggle,
		        "on_scrollbar_changed" : self.adjustmentChanged,
		        "on_spinbutton_changed" : self.adjustmentChanged,
		        "on_scrollbar_colour_changed": self.scrollbarColourScroll,
		        "on_btnVideoDefaults_clicked" : self.resetVideoDefaults,
		        "on_chkForceAspect_toggled" : self.toggleForceAspect,
		        "on_btnClose_clicked" : self.closeWindow }
		self.wTree.signal_autoconnect(dic)
		
		# Create a dictionary for checkboxes and their associated settings.
		self.chkDic = { self.wTree.get_widget('chkInstantSeek') : "gui/instantseek",
		                self.wTree.get_widget('chkDisableXscreensaver') : "misc/disablexscreensaver",
		                self.wTree.get_widget('chkForceAspect') : "video/force-aspect-ratio" }
		# And one for the scrollbars.
		self.adjDic = { self.wTree.get_widget('spnMouseTimeout') : "gui/mousehidetimeout",
		                self.wTree.get_widget('hscBrightness') : "video/brightness",
		                self.wTree.get_widget('hscContrast') : "video/contrast",
		                self.wTree.get_widget('hscHue') : "video/hue",
		                self.wTree.get_widget('hscSaturation') : "video/saturation" }
		
		# More easy access.
		self.window = self.wTree.get_widget(windowname)
		# Set the parent window to the widget passed (hopefully the main window.)
		self.window.set_transient_for(parent)
		
		# Load the preferences.
		self.loadPreferences()
		# Run the dialogue.
		self.window.run()
	
	
	def closeWindow(self, widget, event=None):
		## Destroys the preferences window.
		self.window.destroy()
	
	
	def loadPreferences(self):
		## Reads the preferences from the config and displays them.
		for x in self.chkDic:
			# Set all the checkboxes to their appropriate settings.
			x.set_active(self.cfg.getBool(self.chkDic[x]))
		
		for x in self.adjDic:
			x.set_value(self.cfg.getInt(self.adjDic[x]))
	
	
	def checkboxToggle(self, widget):
		## A generic function called when toggling a checkbox.
		self.cfg.set(self.chkDic[widget], widget.get_active())
	
	def adjustmentChanged(self, widget):
		## A generic function called when scrolling a scrollbar.
		self.cfg.set(self.adjDic[widget], widget.get_value())
	
	
	def scrollbarColourScroll(self, widget):
		## Reads all the colour settings and sets them.
		if (self.player.playingVideo()):
			# Set it if a video is playing.
			self.player.setBrightness(self.cfg.getInt("video/brightness"))
			self.player.setContrast(self.cfg.getInt("video/contrast"))
			self.player.setHue(self.cfg.getInt("video/hue"))
			self.player.setSaturation(self.cfg.getInt("video/saturation"))
	
	
	def resetVideoDefaults(self, widget):
		## Resets all the settings to 0.
		self.wTree.get_widget('hscBrightness').set_value(0)
		self.wTree.get_widget('hscContrast').set_value(0)
		self.wTree.get_widget('hscHue').set_value(0)
		self.wTree.get_widget('hscSaturation').set_value(0)
			
		# Call the colour changed settings so they are changed in the video.
		self.scrollbarColourScroll(widget)
	
	
	def toggleForceAspect(self, widget):
		## Sets force aspect ratio to if it's set or not.
		if (self.player.playingVideo()):
			self.player.setForceAspectRatio(self.cfg.getBool("video/force-aspect-ratio"))



class OpenURI:
	def __init__(self, parent):
		## Creates an openURI dialogue.
		# Create the dialogue.
		dlg = gtk.Dialog(("Input a URI"), parent,
		                  buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
		                             gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		
		# Create the label and entry, then pack them.
		label = gtk.Label("Enter the URI:")
		label.set_alignment(0, 0.5)
		entry = gtk.Entry()
		entry.set_size_request(350, -1)
		dlg.vbox.pack_start(label)
		dlg.vbox.pack_start(entry)
		# Show all the dialogues.
		dlg.show_all()
		
		# Run the dialogue, then hide it.
		res = dlg.run()
		dlg.hide()
		
		# Save the URI if OK was pressed.
		self.URI = entry.get_text() if (res == gtk.RESPONSE_OK) else None
		# Destroy the dialogue.
		dlg.destroy()
		
