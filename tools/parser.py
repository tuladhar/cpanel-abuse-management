"""
parser.py
"""
import os				# os.path.isfile(), os.path.abspath ...
import ConfigParser 	# ConfigParser.RawConfigParser ...
import sys 				# sys.exit() ...

def parse_config(filename):
	"""
	reads given configuration file returns RawConfigParser instance or catches exception and sys.exit's.
	"""
	
	absfilepath = os.path.abspath(filename)							# determine the absolute path of file
	
	if not os.path.isfile(absfilepath):								# make sure file exists on path
	
		print '[x] No such file %s' % filename
		sys.exit(1)

	parser = ConfigParser.RawConfigParser(allow_no_value=1)							# raw config parser instance

	try:

		with open(absfilepath, 'r') as f:							# open the configuration file
			
			parser.readfp(f)										# read the configuration file
			return parser 											# return the parser object

	except ConfigParser.Error as configerror:

		print '[x] Unable to parse configuration file.'
		print '[x] %s' % configerror
		sys.exit(1)

	except AssertionError as asserror:

		print '[x] Name/value missing in the configuration file (%s).' % filename
		print '[x] %s' % asserror
		sys.exit(1)

	except IOError as ioerror:

		print '[x] %s' % ioerror
		sys.exit(1)

	except Exception as exception:

		print '[x] %s' % exception
		sys.exit(1)
		
def validate_config(parser, whm_server, whmcs_server):
	"""
	Function Takes 3 argments
	1) RawConfigParser instance: contains configuration information from configuration file.
	2) WHM Server section name: where required options for that section are asserted.
	3) WHMCS Server section name: where required options for WHMCS section are asserted.

	Eg:
	- To connect to WHM Server, these options are asserted: server, port (defaults to 2087), username and password

	Eg:
	- To connect to WHMCS Server, these options are asserted: server, port, username, password and accesskey
	"""
	try:
		whm_options = ['server', 'port', 'username', 'password']

		## verify options in WHM server section ##
		for option in whm_options:
			assert parser.get(whm_server, option)
		
		whmcs_options = whm_options
		whmcs_options.append('accesskey')		## add accesskey option ##

		## verify options in WHM server section ##
		for option in whmcs_options:
			assert parser.get(whmcs_server, option)

	except AssertionError as asserror:
		print '[x] Option (%s) missing for (%s) server in the configuration file.' % (option, whm_server)
		return False

	except ConfigParser.Error as configerror:
		print '[x] Unable to parse the configuration file.'
		print '[x] %s' % configerror
		return False
	
	## configuration ok ##
	return True
