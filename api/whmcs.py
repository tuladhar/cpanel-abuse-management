"""
Module: whmcs.py
Description: Provides easy access to WHMCS API functions, parses json response and returns data as python dictionary,
			 Error handling and can be easily extended by implementing required API functions."""
import sys						# sys.exit() ...
import hashlib					# hashlib.md5() ...
import urllib2, urllib 			# urllib2.urlopen(), urllib.urlencode() ...
import json						# json.loads() ...
import ssl 						# ssl connection and ssl.SSLError

class WHMCS(object):

	__timeout__ = 120

	def __init__(self, server, port, username, password, accesskey):

		self.server 	= server
		self.port   	= port
		self.username 	= username
		self.password 	= hashlib.md5(password).hexdigest()		# convert password to md5 hash
		self.accesskey 	= accesskey
		self.whmcs_post = {
			'username': self.username,
			'password': self.password,
			'accesskey': self.accesskey,
			'responsetype': 'json'
		}
		self.url = "%s:%s/includes/api.php" % (self.server, self.port)

	def send_request(self, whmcs_post):
		"""
		- WHMCS.send_request() method takes WHMCS url and POST data
		- returns the json response as python dictionary
		"""
		try:
			whmcs_post = urllib.urlencode(whmcs_post)
			json_response = urllib2.urlopen(self.url, whmcs_post, WHMCS.__timeout__).read().encode('utf-8', 'ignore')

			try:
				response = json.loads(json_response)
				return response

			except ValueError as valueerror:
				print '[x] JSON parsing error.'
				print '[x] JSON data: %s' % json_response
				print '[x] %s' % valueerror.message
				return None

		except KeyboardInterrupt:
			print
			return None
		
		except urllib2.URLError as urlerror:
			print '[x] %s' % urlerror
			return 'urlerror'
		
		except ssl.SSLError as sslerror:
			print '[x] ssl: %s' % sslerror
			return 'sslerror '

		except Exception as exception:
			print '[X] exception: %s' % exception
			raise exception

	def getclientsproducts(self, **kwargs):
		"""
		Send [getclientsproducts] API request and return the product/services details associated with the domain
		"""
		whmcs_post = self.whmcs_post
		
		# set action
		whmcs_post['action'] = 'getclientsproducts'
		
		# set action parameters
		whmcs_post.update(kwargs)

		# send request
		response = self.send_request(whmcs_post)

		return response

	def getclientsdetails(self, **kwargs):
		"""
		Send [getclientsdetails] API request and return the client details
		"""
		whmcs_post = self.whmcs_post

		# set action
		whmcs_post['action'] = 'getclientsdetails'

		# set action parameters
		whmcs_post.update(kwargs)

		# send request and return the response
		response = self.send_request(whmcs_post)
		return response

	def updateclientproduct(self, **kwargs):
		"""
		Send [updateclientproduct] API request to WHMCS server
		"""
		# setup POST data
		whmcs_post = self.whmcs_post

		# set action
		whmcs_post['action'] = 'updateclientproduct'

		# set action parameters
		whmcs_post.update(kwargs)

		# send api request and return response
		response = self.send_request(whmcs_post)
		return response

	def getsupportdepartments(self):
		"""
		Send [getsupportdepartments] API Request and return the list of departments list as python dictionary
		"""
		# setup POST field
		whmcs_post = self.whmcs_post

		# set action
		whmcs_post['action'] = 'getsupportdepartments'

		# no set action parameters
		# send request and return the response
		response = self.send_request(whmcs_post)
		return response

	def openticket(self, **kwargs):
		"""
		This command is used to create a new ticket in WHMCS.
		More info: http://docs.whmcs.com/API:Open_Ticket
		"""
		# setup POST field
		whmcs_post = self.whmcs_post

		# set action
		whmcs_post['action'] = 'openticket'

		# set action parameters
		whmcs_post.update(kwargs)

		# send request and return the response

		response = self.send_request(whmcs_post)
		return response

	def addticketreply(self, **kwargs):
		"""
		This command is used to add a reply to an existing ticket.
		More info: http://docs.whmcs.com/API:Reply_Ticket
		"""
		# setup POST field
		whmcs_post = self.whmcs_post

		# set action
		whmcs_post['action'] = 'addticketreply'

		# set action parameters
		whmcs_post.update(kwargs)

		# send request and return response
		response = self.send_request(whmcs_post)
		return response
