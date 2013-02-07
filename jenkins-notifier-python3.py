#!/usr/bin/python3

# apt-get install python3-gi
# 		  python3-urllib3

import notify2
import time 
import urllib3

from gi.repository import Gtk
from gi.repository import GObject
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
	statusIcon = Gtk.StatusIcon()
	notification = None
	lastKnownBuild = None

	def openUrl(self,url):
		conn = urllib3.connection_from_url(url)
		if self.USER is not None:
			base64string = base64.encodestring('{0}:{1}'.format(self.USER, self.PASSWORD)).replace('\n', '')
			return conn.get_url(url, headers={"Authorization","Basic {0}".format(base64string)}).data
		else:
			return conn.get_url(url).data
			

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
		# self.statusIcon.set_tooltip(msg)

	def success(self,lastBuild,changeSet):
		notify = self.statusIconImg != self.SUCCESS_IMG		
		msg = 'Build #' + str(lastBuild) + ' is a Success\n' + changeSet
		print( msg )		
		self.updateStatusIcon(self.SUCCESS_IMG, msg)
		if notify:
			self.notifySuccess(msg)

	def failure(self,lastBuild,changeSet):
		msg = 'Build #' + str(lastBuild) + ' Failed!\n' + changeSet
		print( msg )
		self.updateStatusIcon(self.FAILURE_IMG, msg)
		self.notifyFailure(msg)

	def formatChangeSet(self,buildNo):
		feed = eval(self.openUrl(self.URL + '/' + str(buildNo) + '/api/python').read())
		items = feed['changeSet']['items']
		changeSet = map(lambda item: '- [' + item['author']['fullName'] + '] ' + item['comment'], items)
		return ''.join(changeSet)

	def refresh(self):
		try:
			# print( "refreshing, lastKnownBuild is ", self.lastKnownBuild )
			feed = eval(self.openUrl(self.URL + '/api/python').read())
			lastBuild = feed['lastCompletedBuild']
			# print( "lastBuild is now ", lastBuild )
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
			# return true to keep calling that function, see GObject.timeout_add
			return True

		except urllib3.URLError as error:
			print( "Cannot connect to", self.URL, error.args, error.message )
			self.updateStatusIcon(self.UNKNOWN_IMG, 'Unable to connect to Jenkins, trying later ...')
			return True

		except:
			print( "Got unexpected error!" )
			traceback.print_exc(file=sys.stdout)
			# Initialy I was doing
			# sys.exit()
			# but it turns out some network errors come up as non-URLError
			return True

	def __init__(self):
		notify2.init('Jenkins Notify') 
		self.updateStatusIcon(self.UNKNOWN_IMG, 'Connecting to Jenkins ...')
		GObject.timeout_add(3000, self.refresh)
		Gtk.main()


if __name__ == '__main__': 
	JenkinsNotifier() 
