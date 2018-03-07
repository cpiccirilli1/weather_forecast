#!/usr/bin/python3
'''
version 1.0.2

A custom module made to ease the writing of data.
'''

import requests, sys

class Writer:

	def __init__(self, title=None, src=None, bit = 1024, text = None):
		self.title = title
		self.src = src
		self.bit = bit

	def fileWriter(self):
		title = isstring(self.title)
		if (self.title == None) | (self.src == None):
			print('This requires both a TITLE and SOURCE.')
			return
		elif not title:
			print('Title Must Be A String!')
			return
		else:	
			req = requests.get(self.src)

			with open(self.title, 'wb') as f:

				for chunk in req.iter_content(self.bit):
					f.write(chunk) 
			return		
					
	def txtWriter(self, mode="w", text=None):
		file = isstring(self.title)
		text_check = isstring(text)
		if not file:
			print('File Name is not a String.')
			return
		elif not text_check:
			print('Text is not a string.')
			return
		else:	
			with open(self.title, mode) as fn:
				fn.write(text)

	def txtReader(self, mode="r"):
		file = isstring(self.title)
		if not file:
			print('Text is not a string.')
		else:
			with open(self.title, mode) as read_file:
				lines = read_file.readlines()
			return lines					

def isstring(s):
    # if we use Python 3
    if (sys.version_info[0] >= 3):
        return isinstance(s, str)
    # we use Python 2
    return isinstance(s, basestring)