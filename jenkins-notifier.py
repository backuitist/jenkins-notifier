#!/usr/bin/python

import pynotify 
import time 
import urllib
import pygtk
pygtk.require('2.0')
import gtk
import gobject
import os

class JenkinsNotifier:
	JOB = 'Backuity'
	URL = 'http://localhost:8080/job/backuity'
	dir_path = os.path.dirname(__file__)
	SUCCESS_IMG = os.path.abspath(dir_path + '/jenkins-green.png')
	FAILURE_IMG = os.path.abspath(dir_path + '/jenkins-red.png')
	UNKNOWN_IMG = os.path.abspath(dir_path + '/jenkins-grey.png')
	statusIconImg = UNKNOWN_IMG
	statusIcon = gtk.StatusIcon()

	def notifySuccess(self,msg): 
		n = pynotify.Notification(self.JOB, 
			msg, self.SUCCESS_IMG) 
		n.set_urgency(pynotify.URGENCY_LOW) 
		n.show() 

	def notifyFailure(self,msg): 
		n = pynotify.Notification(self.JOB, 
			msg, self.FAILURE_IMG) 
		n.set_urgency(pynotify.URGENCY_CRITICAL) 
		n.show() 

	def updateStatusIcon(self, icon, msg):
		self.statusIconImg = icon
		self.statusIcon.set_from_file(icon)
		self.statusIcon.set_tooltip(msg)

	def success(self,lastBuild):
		if self.statusIconImg != self.SUCCESS_IMG:
			msg = 'Build #' + lastBuild + ' is a Success'
			self.updateStatusIcon(self.SUCCESS_IMG, msg)
			self.notifySuccess(msg)

	def failure(self,lastBuild):
		if self.statusIconImg != self.FAILURE_IMG:
			msg = 'Build #' + str(lastBuild) + ' Failed!'
			self.updateStatusIcon(self.FAILURE_IMG, msg)
			self.notifyFailure(msg)

	def refresh(self):
		feed = eval(urllib.urlopen(self.URL + '/api/python').read())
		lastBuild = feed['lastBuild']['number']
		if lastBuild != self.lastKnownBuild:
			self.lastKnownBuild = lastBuild			
			lastSuccess = feed['lastSuccessfulBuild']
			if lastSuccess == None or lastSuccess['number'] != lastBuild:
				self.failure(lastBuild)
			else:
				self.success(lastBuild)
		# return true to keep calling that function, see gobject.timeout_add
		return True

	def __init__(self):
		pynotify.init('Jenkins Notify') 
		self.updateStatusIcon(self.UNKNOWN_IMG, 'Connecting to Jenkins ...')
		self.lastKnownBuild = -1
		gobject.timeout_add(3000, self.refresh)
		gtk.main()


if __name__ == '__main__': 
	JenkinsNotifier() 
