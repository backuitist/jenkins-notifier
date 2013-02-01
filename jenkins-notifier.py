#!/usr/bin/python

import pynotify 
import time 
import urllib
import pygtk
pygtk.require('2.0')
import gtk
import gobject
import os
import sys
import traceback

class JenkinsNotifier:
	JOB = 'Backuity'
	URL = 'http://localhost:8080/job/backuity'
	dir_path = os.path.dirname(__file__)
	SUCCESS_IMG = os.path.abspath(dir_path + '/jenkins-green.png')
	FAILURE_IMG = os.path.abspath(dir_path + '/jenkins-red.png')
	UNKNOWN_IMG = os.path.abspath(dir_path + '/jenkins-grey.png')
	statusIconImg = UNKNOWN_IMG
	statusIcon = gtk.StatusIcon()
	notification = None
	lastKnownBuild = None

	def notifySuccess(self,msg): 
		self.closeNotification()
		self.notification = pynotify.Notification(self.JOB, 
			msg, self.SUCCESS_IMG) 
		self.notification.set_urgency(pynotify.URGENCY_LOW) 
		self.notification.show() 

	def closeNotification(self):
		if self.notification is not None:
			self.notification.close()

	def notifyFailure(self,msg):
		self.closeNotification() 
		self.notification = pynotify.Notification(self.JOB, 
			msg, self.FAILURE_IMG) 
		self.notification.set_urgency(pynotify.URGENCY_CRITICAL) 
		self.notification.show() 

	def updateStatusIcon(self, icon, msg):
		self.statusIconImg = icon
		self.statusIcon.set_from_file(icon)
		self.statusIcon.set_tooltip(msg)

	def success(self,lastBuild):
		if self.statusIconImg != self.SUCCESS_IMG:
			msg = 'Build #' + str(lastBuild) + ' is a Success'
			print msg
			self.updateStatusIcon(self.SUCCESS_IMG, msg)
			self.notifySuccess(msg)

	def failure(self,lastBuild):
		msg = 'Build #' + str(lastBuild) + ' Failed!'
		print msg
		self.updateStatusIcon(self.FAILURE_IMG, msg)
		self.notifyFailure(msg)

	def refresh(self):
		try:
			# print "refreshing, lastKnownBuild is ", self.lastKnownBuild
			feed = eval(urllib.urlopen(self.URL + '/api/python').read())
			lastBuild = feed['lastCompletedBuild']
			# print "lastBuild is now ", lastBuild
			if lastBuild is not None:
				lastBuild = lastBuild['number']

				if lastBuild != self.lastKnownBuild:

					self.lastKnownBuild = lastBuild			
					lastSuccess = feed['lastSuccessfulBuild']
					# print "Last success", lastSuccess
					if lastSuccess is None or lastSuccess['number'] != lastBuild:
						self.failure(lastBuild)
					else:
						self.success(lastBuild)
				# return true to keep calling that function, see gobject.timeout_add
			return True
		except:
			traceback.print_exc(file=sys.stdout)
			sys.exit()

	def __init__(self):
		pynotify.init('Jenkins Notify') 
		self.updateStatusIcon(self.UNKNOWN_IMG, 'Connecting to Jenkins ...')
		gobject.timeout_add(3000, self.refresh)
		gtk.main()


if __name__ == '__main__': 
	JenkinsNotifier() 
