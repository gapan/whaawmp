#!/usr/bin/env python

#  A few useful functions for Whaaw! Media Player.
#  Copyright (C) 2007, Jeff Bailes <thepizzaking@gmail.com>
#
#       This program is free software: you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation, either version 3 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program.  If not, see <http://www.gnu.org/licenses/>.

def nsTos(ns):
	## Converts nanoseconds to seconds.
	return ns / 1000000000

def secToStr(s):
	## Converts seconds into a string of H:M:S
	h = s / 3600
	m = (s % 3600) / 60
	s = s % 60
	# Only print hours if it doesn't equal 0.
	if (h != 0):
		return '%d:%02d:%02d' % (h, m, s)
	else:
		return '%d:%02d' % (m, s)

def toRange(val, min, max):
	## Returns a value within the requested range. ie, checks that val
	## lies within it, if it doesn't make is so.
	if (val < min): val = min
	if (val > max): val = max
	return val
