#!/usr/bin/python

import pynotify
import time 
import urllib3

from urllib3.exceptions import HTTPError

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import os
import sys
import traceback
import base64

class JenkinsNotifier:
	JOB = 'Backuity'

	URL = 'http://localhost:8080/job/backuity'
	# use None if no authentication is needed
	USER = 'admin'
	# API token, see http://localhost:8080/user/admin/configure (replace admin by the user)
	PASSWORD = '7ec35dc206ffb7ae840a2311d7741111'

	dir_path = os.path.dirname(__file__)
	SUCCESS_IMG = os.path.abspath(dir_path + '/jenkins-green.png')
	FAILURE_IMG = os.path.abspath(dir_path + '/jenkins-red.png')
	UNKNOWN_IMG = os.path.abspath(dir_path + '/jenkins-grey.png')

	statusIconImg = UNKNOWN_IMG
	statusIcon = gtk.StatusIcon()
	notification = None
	lastKnownBuild = None

	def openUrl(self,url):
		conn = urllib3.connection_from_url(url)
		if self.USER is not None:
			authHeaders = urllib3.util.make_headers(basic_auth='%s:%s' % (self.USER, self.PASSWORD))
			return conn.request('GET',url, headers=authHeaders).data
		else:
			return conn.get_url('GET',url).data
			

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

	def success(self,lastBuild,changeSet):
		notify = self.statusIconImg != self.SUCCESS_IMG		
		msg = 'Build #' + str(lastBuild) + ' is a Success\n' + changeSet
		print msg
		self.updateStatusIcon(self.SUCCESS_IMG, msg)
		if notify:
			self.notifySuccess(msg)

	def failure(self,lastBuild,changeSet):
		msg = 'Build #' + str(lastBuild) + ' Failed!\n' + changeSet
		print msg
		self.updateStatusIcon(self.FAILURE_IMG, msg)
		self.notifyFailure(msg)

	def formatChangeSet(self,buildNo):
		feed = eval(self.openUrl(self.URL + '/' + str(buildNo) + '/api/python'))
		items = feed['changeSet']['items']
		changeSet = map(lambda item: '- [' + item['author']['fullName'] + '] ' + item['comment'], items)
		return ''.join(changeSet)

	def jenkinsError(self,msg):
		self.updateStatusIcon(self.UNKNOWN_IMG, msg)
		self.lastKnownBuild = None


	def refresh(self):
		try:
			# print "refreshing, lastKnownBuild is ", self.lastKnownBuild
			feed = eval(self.openUrl(self.URL + '/api/python'))
			lastBuild = feed['lastCompletedBuild']
			# print "lastBuild is now ", lastBuild
			if lastBuild is not None:
				lastBuild = lastBuild['number']

				if lastBuild != self.lastKnownBuild:

					self.lastKnownBuild = lastBuild			
					lastSuccess = feed['lastSuccessfulBuild']
					changeSet = self.formatChangeSet(lastBuild)
					# print "Last success", lastSuccess
					if lastSuccess is None or lastSuccess['number'] != lastBuild:
						self.failure(lastBuild,changeSet)
					else:
						self.success(lastBuild,changeSet)
			# return true to keep calling that function, see gobject.timeout_add
			return True

		except HTTPError, error:
			print "Connection error", error.message
			self.jenkinsError('Unable to connect to Jenkins, trying later ...')
			return True
		
		except SyntaxError, error:
			print "Cannot parse Jenkins results, probably starting up.", error.message
			self.jenkinsError('Cannot parse Jenkins results (probably starting up), trying later ...')
			return True

		except:
			print "Got unexpected error!"
			traceback.print_exc(file=sys.stdout)
			sys.exit()

	def __init__(self):
		pynotify.init('Jenkins Notify') 
		self.updateStatusIcon(self.UNKNOWN_IMG, 'Connecting to Jenkins ...')
		gobject.timeout_add(3000, self.refresh)
		gtk.main()


if __name__ == '__main__': 
	JenkinsNotifier() 
