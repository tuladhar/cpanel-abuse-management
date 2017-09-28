"""
Module: cpanelapi.py
Description: Provides easy access to cPanel API functions, parses json response and returns data as python dictionary,
			 Error handling and can be easily extended by implementing required API functions.
"""
from sys import exit
import sys			# sys.exit()
import base64		# base64.b64encode() ...
import urllib, urllib2 # urllib2.Request(), urllib2.urlopen(), urllib.quote ...
import json 		# json.loads() ...
import ssl 			# required for https request and ssl errors

class cPanel(object):

	__timeout__ = 120

	def __init__(self, server, port, username, password):
		self.server 	 = server
		self.port 		 = port
		self.username 	 = username
		self.password 	 = password
		self.headers = {
			"Authorization": "Basic %s" % base64.b64encode('%s:%s' % (username, password))
		}
		self.url_prefix  = "%s:%s/json-api" % (server, port)

	@staticmethod
	def send_request(request):
		"""
		- sendrequest() function takes urllib2.Request object
		- returns json response data as python dictionary.
		"""
		try:
			json_response = urllib2.urlopen(request, '', cPanel.__timeout__).read().encode('utf-8', 'ignore')
			
			try:
				response = json.loads(json_response)
				return response

			except ValueError as valueerror:
				print '[x] JSON parsing error.'
				print '[x] JSON data: %s' % json_response
				print '[x] %s' % valueerror.message
				return None

		except KeyboardInterrupt: print; return None
		
		except urllib2.URLError as urlerror:
			print '[x] %s' % urlerror
			return 'urlerror'
		
		except ssl.SSLError as sslerror:
			print '[x] %s' % sslerror
			return 'urlerror'

		except Exception as ex:
			print '[x] %s' % ex.message
			return None

	def listacct(self, searchtype='', search=''):
		"""
		Sends [listacct] API request with given search_type and search_term and returns result as python dictionary
		"""

		# setup api request
		url = '%s/listaccts?searchtype=%s&search=%s' % (self.url_prefix, searchtype, search)
		request = urllib2.Request(url, data={}, headers=self.headers)

		# send api request and return response
		response = cPanel.send_request(request)
		return response

	def suspendacct(self, user='', reason=''):
		"""
		Send [suspendacct] API request and suspend the given cPanel user with reason.
		"""
		# setup api request
		reason = urllib.quote(reason)
		url = '%s/suspendacct?user=%s&reason=%s' % (self.url_prefix, user, reason)
		request = urllib2.Request(url, {}, self.headers)

		# send api request and return response
		response = cPanel.send_request(request)
		return response

	def unsuspendacct(self, user=''):
		"""
		Send [unsuspendacct] API request and unsuspend given user cPanel account
		"""
		# setup api request
		url = '%s/unsuspendacct?user=%s' % (self.url_prefix, user)
		request = urllib2.Request(url, {}, self.headers)
		
		# send request and return response
		response = cPanel.send_request(request)
		return response
