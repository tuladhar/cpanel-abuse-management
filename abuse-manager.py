#!/usr/bin/env python
# *-* coding: utf-8 *-*
#
# abuse-manager.py v1.1 <purshottam.tuladhar@nepallink.net>
#
# This program automates the abusing cPanel and WHMCS accounts by suspending (cPanel & WHMCS Product/Services) 
# and opens WHMCS ticket to abuse department.
#
# Tested on Python v2.7.x
__program__='abuse-manager.py'
__version__="1.1"
__usage__='''\
Usage: python {prog} [-c config_file] [-s server_name] 
       [--search domain|username] [--subject subject_title]
       [-m ticket_template] [-r suspend_template] [-f abuse_proof_file]
       [--allyes]

Try 'python {prog} --help' for more options.'''.format(prog=__program__)
__email__="purshottam.tuladhar@nepallink.net"
start=0

# GLOBALS
opts=None				# OptionParser instance
whmcs=cpanel=None		# whmcs and cPanel api instance

try:
	# standard library modules
	from sys import exit
	import sys, optparse, time, re, string

	# custom modules
	from tools.parser import parse_config, validate_config
	from api.whmcs import WHMCS
	from api.cpanel import cPanel

except ImportError as importerror:
	print ('[x] %s' % importerror)
	exit(0)

def build_cmdline():
	"""
	creates OptionParser instance and populates command-line options
	and returns OptionParser instance (cmd)
	"""
	cmd=optparse.OptionParser(version=__version__)
	cmd.add_option('-c', '', dest='config_fname',type="string", help='WHM/WHMCS configuration file', metavar="FILE")
	cmd.add_option('-s', '', dest="whm_section", type="string", help="WHM server to use. Specify section name. eg: -s ds01", metavar="SERVER")
	cmd.add_option('','--search', action="store", dest='search', type="string", help="Search client by DNS domain name or cPanel username", metavar="STRING")
	cmd.add_option('-d', '', dest='whmcs_deptid', type="int", help="WHMCS Department ID", metavar="INT") 
	cmd.add_option('-m', '', dest='whmcs_ticketmsg_fname', type="string", help="WHMCS abuse ticket template file", metavar='FILE')
	cmd.add_option('-r', '', dest='whm_suspendmsg_fname', type="string", help='cPanel account suspension reason template file', metavar='FILE')
	cmd.add_option('-f', '', dest='whmcs_proofmsg_fname', type="string", help='Abuse proof file which will be appended to abuse ticket message', metavar='FILE')
	cmd.add_option('', '--subject', dest='whmcs_subject', type="string", help='Specify abuse ticket subject title.', metavar="STRING")
	cmd.add_option('-y', '--allyes', dest='allyes', action="store_true", default=False, help='Assume yes as an answer to any question which would be asked')
	return cmd

def display_departmentlist():
	"""
	returns department id selected by the user from department list prompt.
	"""
	deptid = 0
	print
	print '[*] Fetching departments list'

	# call the api function
	supportdepartments = whmcs.getsupportdepartments()
	if supportdepartments == None:
		print '[x] WHMCS getsupportdepartments API function call failed.'
		print '[!] exiting.'
		_exit(0)

	# reconnect if ssl or url error orccured
	while supportdepartments == 'sslerror' or supportdepartments == 'urlerror':
		print '[!] Re-establishing connection after 5 seconds'
		try: time.sleep(5)
		except KeyboardInterrupt: print '\n[!] exiting.'; _exit()
		supportdepartments = whmcs.getsupportdepartments()

	result = supportdepartments.get('result')
	totalresults = supportdepartments.get('totalresults')
	if result != 'success' or totalresults == 0:
		print '[x] Unable to find any support departments on (%s).' % (parser.get('whmcs', 'server'))
		print '[x] %s.' % supportdepartments.get('message')
		_exit()

	#############################
	## Display Department List ##
	#############################
	# Eg: {'departments': { 'department': [{'id': ,'name': ,'awaitingreply': ,'opentickets': ,}, {...}]}}

	departments = supportdepartments.get('departments').get('department')
	rowformat = '| %-5s | %-20s | %-15s | %-15s |'
	header = ('ID', 'Department', 'Awaiting Reply', 'Open Tickets')
	title = rowformat % header
	print '-' * len(title)
	print title
	print '-' * len(title)
	deptlist = []
	for department in departments:
		deptid = department['id']
		deptlist.append(deptid)
		deptname=department['name']
		if len(deptname) > 20:
			deptname = deptname[:20-4]+'...'
		print rowformat % (deptid, deptname, department.get('awaitingreply'), department.get('opentickets'))
		print '-' * len(title)

	# Display department ID selection prompt
	while 1:
		try:
			deptid = raw_input('[+] Select Department ID: ')
		except KeyboardInterrupt:
			print '\n[!] exiting.cleanly.'
			exit()

		if type(deptid) != int and deptid not in deptlist:
			print '[!] Invalid Department ID (%s).' % deptid
		else:
			break
	return deptid

def suspend_cpanel(listacct, openticket):
	"""
	helper cPanel account suspending function
	"""
	print
	print '[*] Suspending cPanel account (%s)' % listacct.get('user')

	# setup template variable replacement
	vars = {
		'ticket_id': openticket.get('tid'),
		'ticket_id2': openticket.get('id')
	}
	template = string.Template(opts.whm_suspendmsg)
	suspendmsg = template.safe_substitute(vars)

	# invoke suspendacct api function
	suspendacct = cpanel.suspendacct(listacct.get('user'), suspendmsg)
	if suspendacct == None:
		print '[x] WHM suspendacct API function call failed.'
		print '[!] exiting.'
		_exit()

	# reconnect if ssl or url error orccured
	while suspendacct == 'sslerror' or suspendacct == 'urlerror':
		print '[!] Re-establishing connection after 5 seconds'
		try: time.sleep(5)
		except KeyboardInterrupt: print '\n[!] exiting.'; _exit()
		suspendacct = cpanel.suspendacct(listacct.get('user'), suspendmsg)

	result = suspendacct.get('result')[0]
	status = result.get('status')

	if status == 0:
		print '[!] Unable to suspend cPanel account (%s) of domain (%s)' % (listacct.get('user'), listacct.get('domain'))
		print '[x] %s' % result.get('statusmsg')
		print
		if not opts.allyes:
			ans=raw_input('[?] Do you want to continue, opening ticket [y/N]: ')
			if not ans.lower() in ['y', 'yes']:
				print '[!] exiting.cleanly.'
				exit(0)
	else:
		print '[!] Account successfully suspended.'

def start_timer():
	global start
	start = int(time.strftime('%S'))

def _exit():
	end = int(time.strftime('%S'))
	print
	print '[Finished in ~%.1fs]' % abs((end - start))
	exit(0)

def main():
	# external functions needs to access
	# these variables, make changes globally
	global cpanel, whmcs, opts

	# console output formatter
	format = '-->%15s: %s'

	# display usage/help
	if len(sys.argv) == 1:
		print __usage__
		exit(0)

	# generate the command-line options
	# and parse those options
	opts, args = build_cmdline().parse_args()

	# set opening ticket subject title or set const title
	if not opts.whmcs_subject:
		opts.whmcs_subject = "Abuse and Suspension Notice"

	# filter required options
	require_opts = {
		'-c [configuration_filename]': opts.config_fname,
		'-s [server_name]': opts.whm_section,
		'--search [client domain|username]': opts.search,
		'-m [openticket_template]': opts.whmcs_ticketmsg_fname,
		'-r [cpanelsuspend_template]': opts.whm_suspendmsg_fname
	}
	for option, value in require_opts.items():
		if value == None:
			o = """{p}: '{opt}' option missing.\n\nTry 'python {p} --help' for more options.""".format(p=__program__, opt=option)
			print (o)
			exit(0)

	#####################
	#  BEGIN EXECUTION  #
	#####################
	current_time = "%s %s" % (time.strftime('%F %H:%M'), time.tzname[0])
	print 'Starting %s v%s [ %s ]' % (__program__, __version__, current_time)
	start_timer()

	# parse configuration file
	parser = parse_config(opts.config_fname)

	# validate configuration files
	validate_config(parser, opts.whm_section, 'whmcs')

	# read the template file
	try:
		# WHMCS opening ticket template
		with open(opts.whmcs_ticketmsg_fname, 'r') as f1:
			opts.whmcs_ticketmsg = f1.read().strip()

		# WHM cPanel suspension reason template
		with open(opts.whm_suspendmsg_fname, 'r') as f2:
			opts.whm_suspendmsg = f2.read().strip()
		
		# WHM cPanel suspension proof template
		if opts.whmcs_proofmsg_fname != None:
			with open(opts.whmcs_proofmsg_fname, 'r') as f3:
				opts.whmcs_proofmsg = f3.read().strip()

	except IOError as ioerror:
		print '[x] %s' % ioerror
		exit(1)

	# set client search type
	if '.' in opts.search: opts.searchtype = 'domain'
	else: opts.searchtype = 'user'

	# setup cPanelAPI instance
	server   = parser.get(opts.whm_section, 'server')
	port 	 = parser.get(opts.whm_section, 'port')
	username = parser.get(opts.whm_section, 'username')
	password = parser.get(opts.whm_section, 'password')
	cpanel = cPanel(server, port, username, password)

	# setup cPanelAPI instance
	server   = parser.get('whmcs', 'server')
	port 	 = parser.get('whmcs', 'port')
	username = parser.get('whmcs', 'username')
	password = parser.get('whmcs', 'password')
	accesskey = parser.get('whmcs', 'accesskey')
	whmcs = WHMCS(server, port, username, password, accesskey)

	###########################
	## Search cPanel account ##
	###########################
	print
	print '[*] Searching cPanel account (%s) [%s]' % (opts.search, parser.get(opts.whm_section, 'server'))
	
	listacct = cpanel.listacct(searchtype=opts.searchtype, search=opts.search)
	if listacct == None:
		print '[x] WHM listacct API function call failed.'
		print '[!] exiting.'
		_exit()
	
	# reconnect if ssl or url error occured
	while listacct == 'sslerror' or listacct == 'urlerror':
		print '[!] Re-establishing connection after 5 seconds'
		try: time.sleep(5)
		except: print '\n[!] exiting.'; _exit()
		listacct = cpanel.listacct(searchtype=opts.searchtype, search=opts.search)

	# get the listacct call response status
	status = listacct.get('status')
	acct   = listacct.get('acct')

	############################
	## Display cPanel account ##
	############################
	if status == 1 and len(acct) == 1:
		# assign the acct[0] dictionary to listacct
		listacct = acct[0]

		print format % ('Domain', listacct.get('domain'))
		print format % ('IP', listacct.get('ip'))
		print format % ('Username', listacct.get('user'))
		print format % ('Owner', listacct.get('owner'))
		print format % ('Owner Email', listacct.get('email'))
		if listacct.get('suspended'):
			print format % ('Suspend Reason', listacct.get('suspendreason').replace('\n', ' '))
			print '[!] Account already suspended.'
			_exit()
	else:
		print '[!] No results found.'
		_exit()

	############################
	## Determine the reseller ##
	############################
	owner_nepallink = re.search('(root|npvps01)', listacct.get('owner'))

	###############################################
	# Nepallink is the reseller for this account ##
	###############################################
	if owner_nepallink:
		"""
		Both cPanel account and Domain product/services should be suspended/activated.
		"""
		#################################
		## Search WHMCS product detail ##
		#################################
		print
		print '[*] Searching product/services (%s) [%s]' % (listacct.get('domain'), whmcs.server)
		
		# invoke WHMCS api function
		clientsproducts = whmcs.getclientsproducts(domain=listacct.get('domain'))
		if clientsproducts == None:
			print '[x] WHMCS getclientsproducts API function call failed.'
			print '[!] exiting.'
			_exit()

		# reconnect if ssl or url error orccured
		while clientsproducts == 'sslerror' or clientsproducts == 'urlerror':
			print '[!] Re-establishing connection after 5 seconds'
			try: time.sleep(5)
			except: print '\n[!] exiting.'; _exit()
			clientsproducts = whmcs.getclientsproducts(domain=listacct.get('domain'))

		result = clientsproducts.get('result')
		# exit if failed response received
		if result != 'success':
			print '[x] %s' % (clientsproducts.get('message'))
			_exit()

		totalresults = int(clientsproducts.get("totalresults"))

		if totalresults == 0:
			print '[x] No product/services found for the domain (%s).' % (listacct.get('domain'))
			_exit()
		elif totalresults > 1:
			print '[!] More than 1 product/services found for domain (%s).' % (listacct.get('domain'))
			_exit()

		# Eg: { "products": { "product": [] } }
		product = clientsproducts.get("products").get("product")[0]

		##################################
		## Display WHMCS product detail ##
		##################################
		print format % ('Product Name', product.get('name'))
		print format % ('Product ID', product.get('pid'))
		print format % ('Service ID', product.get('id'))
		print format % ('Product Status', product.get('status'))

		if product.get('status') == 'Suspended':
			print '[!] Product/Services for domain (%s) already suspended.' % listacct.get('domain')
			print '[!] exiting.'
			_exit()

		################################
		## Fetch WHMCS client details ##
		################################
		print
		print '[*] Fetching WHMCS client details (%s) [%s]' % (listacct.get('domain'), 
			parser.get('whmcs', 'server'))

		# invoke api function
		clientdetails = whmcs.getclientsdetails(clientid=product.get('clientid'))
		if clientdetails == None:
			print '[x] WHMCS getclientsdetails API function call failed.'
			print '[!] exiting.'
			_exit()

		# reconnect if ssl or url error orccured
		while clientdetails == 'sslerror' or clientdetails == 'urlerror':
			print '[!] Re-establishing connection after 5 seconds'
			try: time.sleep(5)
			except: print '\n[!] exiting.'; _exit()
			clientdetails = whmcs.getclientsdetails(clientid=product.get('clientid'))

		result = clientdetails.get('result')
		if result != 'success':
			print '[!] Unable to fetch client detail associated with domain (%s).' % (listacct.get('domain'))
			print '[x] %s' % (clientdetails.get('message'))
			_exit()

		##################################
		## Display WHMCS client detail  ##
		##################################
		fullname = "%s %s" % (clientdetails.get('firstname' ), clientdetails.get('lastname'))
		print format % ('Name', fullname)
		print format % ('User ID', clientdetails.get('userid'))
		print format % ('Email', clientdetails.get('email'))
		print format % ('Company', clientdetails.get('companyname'))
		print format % ('Country', clientdetails.get('countryname'))
		print format % ('Status', clientdetails.get('status'))

		# Prompt for confirmation
		if not opts.allyes:
			print
			try: ans=raw_input('[?] Suspend WHMCS Product/Services, cPanel account and Issue abuse ticket [y/N]: ')
			except: print '\n[!] exiting.'; _exit()

			if not ans.lower() in ['y', 'yes']:
				print '[!] exiting.cleanly.'; _exit()
				exit(0)

		##############################
		## Suspend Product/Services ##
		##############################
		print
		print '[*] Suspending product/services (%s) [%s]' % (product.get('name'), whmcs.server)

		# invoke api call
		suspendproduct = whmcs.updateclientproduct(serviceid=product.get('id'), pid=product.get('pid'),
											  domain=listacct.get('domain'), status='Suspended')
		if suspendproduct == None:
			print '[x] WHMCS updateclientproduct API function call failed.'
			print '[!] exiting.'
			_exit()

		# reconnect if ssl or url error orccured
		while suspendproduct == 'sslerror' or suspendproduct == 'urlerror':
			print '[!] Re-establishing connection after 5 seconds'
			try: time.sleep(5)
			except: print '\n[!] exiting.'; _exit()
			suspendproduct = whmcs.updateclientproduct(serviceid=product.get('id'), pid=product.get('pid'),
											  domain=listacct.get('domain'), status='Suspended')

		result = suspendproduct.get('result')
		if result != 'success':
			print '[x] Unable to suspend product/services (%s) of domain (%s).' % (product.get('name'), listacct.get('domain'))
			print '[x] %s' % suspendproduct.get('message')
			print '[!] exiting.'
			_exit()

		#################
		## Open Ticket ##
		#################
		print
		print '[*] Opening ticket' 

		#########################
		## Get Department List ##
		#########################
		if not opts.whmcs_deptid:
			opts.whmcs_deptid=display_departmentlist()
			print

		print '[!] Please wait...'
		if not opts.whmcs_proofmsg_fname:
			proofmsg = ''
		else:
			proofmsg = "-- CAUSE --\n%s\n""" % opts.whmcs_proofmsg
 		
 		# setup template variable replacement
		vars = {
			'cpanel_user': listacct.get('user'),
			'domain_name': listacct.get('domain'),
			'client_name': string.capwords("%s %s" % (clientdetails['firstname'], clientdetails['lastname'])),
			'proof_message': proofmsg
		}
		template  = string.Template(opts.whmcs_ticketmsg)
		ticketmsg = template.safe_substitute(vars)
		
		# invoke api function
		openticket = whmcs.openticket(clientid=product.get('clientid'), deptid=opts.whmcs_deptid,
									  subject=opts.whmcs_subject, priority="High", message=ticketmsg)
		if openticket == None:
			print '[x] WHMCS openticket API function call failed.'
			print '[!] exiting.'
			_exit()

		result = openticket.get('result')
		if result != 'success':
			print '[x] Unable to issue ticket using clientID (%s) to domain (%s)' % (product.get('clientid'), listacct.get('domain'))
			print '[x] %s' % openticket.get('message')
			_exit()

		print '[!] New Ticket (#%s) has been issued.' % openticket.get('tid')

		####################
		## Suspend cPanel ##
		####################
		suspend_cpanel(listacct, openticket)

	###################################################
	# Nepallink is not the reseller for this account ##
	###################################################
	elif not owner_nepallink:
		"""
		Domain doesn't have product/services, suspend cPanel
		and issue new ticket to the reseller account.
		"""
		if listacct.get('user') != listacct.get('owner') :
			#############################
			## Fetch reseller's cPanel ##
			#############################
			opts.searchtype = 'user'			 # search type
			opts.search = listacct.get('owner')  # reseller's cPanel user name

			print
			print "[*] Retrieving (%s) owner cPanel account [%s]" % (listacct.get('domain'), cpanel.server)

			# invoke api function
			listacct2 = cpanel.listacct(searchtype=opts.searchtype, search=opts.search)
			if listacct2 == None:
				print '[x] WHM listacct API function call failed.'
				print '[!] exiting.'
				_exit()

			# reconnect if ssl or url error orccured
			while listacct2 == 'sslerror' or listacct2 == 'urlerror':
				print '[!] Re-establishing connection after 5 seconds'
				try: time.sleep(5)
				except: print '\n[!] exiting.'; _exit()
				listacct2 = cpanel.listacct(searchtype=opts.searchtype, search=opts.search)

			# get the api response status
			status = listacct2.get('status')
			acct   = listacct2.get('acct')

			if status == 1 and len(acct) == 1:
				# assign the acct[0] dictionary to listacct
				listacct2 = acct[0]
				
				print format % ('Domain', listacct2.get('domain'))
				print format % ('IP', listacct2.get('ip'))
				print format % ('Username', listacct2.get('user'))
				print format % ('Owner', listacct2.get('owner'))
				print format % ('Owner Email', listacct2.get('email'))
				if listacct2.get('suspended'):
					print format % ('Suspend Reason', listacct2.get('suspendreason'))
					print '[!] Reseller account is suspended, unable to suspend client account (%s).' % listacct.get('user')
					print '[!] exiting.'
					_exit()
			else:
				print '[!] No results found.'
				_exit()
		else:
			listacct2 = listacct

		#################################
		## Search WHMCS product detail ##
		#################################
		print
		print '[*] Searching WHMCS product/services (%s) [%s]' % (listacct.get('domain'), whmcs.server)
	
		clientsproducts2 = whmcs.getclientsproducts(domain=listacct2.get('domain'))
		if clientsproducts2 == None:
			print '[x] WHMCS getclientsproducts API function call failed.'
			print '[!] exiting.'
			_exit()

		# reconnect if ssl or url error orccured
		while clientsproducts2 == 'sslerror' or clientsproducts2 == 'urlerror':
			print '[!] Re-establishing connection after 5 seconds'
			try: time.sleep(5)
			except: print '\n[!] exiting.'; _exit()
			clientsproducts2 = whmcs.getclientsproducts(domain=listacct2.get('domain'))

		result = clientsproducts2.get('result')
		# exit if failed response received
		if result != 'success':
			print '[x] %s' % (clientsproducts2.get('message'))
			_exit()

		totalresults = int(clientsproducts2.get("totalresults"))

		if totalresults == 0:
			print '[x] No product/services found for the domain (%s).' % (listacct2.get('domain'))
			_exit()

		# Eg: { "products": { "product": [] } }
		product = clientsproducts2.get("products").get("product")[0]

		##################################
		## Display WHMCS product detail ##
		##################################
		print format % ('Product Name', product.get('name'))
		print format % ('Product ID', product.get('pid'))
		print format % ('Service ID', product.get('id'))
		print format % ('Product Status', product.get('status'))

		if product.get('status') == 'Suspended':
			print '[!] Product/Services for domain (%s) already suspended.' % listacct.get('domain')
			print '[!] exiting.'
			_exit()

		################################
		## Fetch WHMCS client details ##
		################################
		print
		print '[*] Fetching WHMCS client details (%s) [%s]' % (listacct2.get('domain'), 
			parser.get('whmcs', 'server'))

		clientdetails = whmcs.getclientsdetails(clientid=product.get('clientid'))
		if clientdetails == None:
			print '[x] WHMCS getclientsdetails API function call failed.'
			print '[!] exiting.'
			_exit()

		# reconnect if ssl or url error orccured
		while clientdetails == 'sslerror' or clientdetails == 'urlerror':
			print '[!] Re-establishing connection after 5 seconds'
			try: time.sleep(5)
			except: print '\n[!] exiting.'; _exit()
			clientdetails = whmcs.getclientsdetails(clientid=product.get('clientid'))

		result = clientdetails.get('result')
		if result != 'success':
			print '[!] Unable to fetch client detail associated with domain (%s).' % (listacct.get('domain'))
			print '[x] %s' % (clientdetails.get('message'))
			_exit()


		##################################
		## Display WHMCS client detail  ##
		##################################
		fullname = "%s %s" % (clientdetails.get('firstname' ), clientdetails.get('lastname'))
		print format % ('Name', fullname)
		print format % ('User ID', clientdetails.get('userid'))
		print format % ('Email', clientdetails.get('email'))
		print format % ('Company', clientdetails.get('companyname'))
		print format % ('Country', clientdetails.get('countryname'))
		print format % ('Status', clientdetails.get('status'))


		# Prompt for confirmation
		if not opts.allyes:
			print
			try: ans=raw_input('[?] Suspend cPanel account and issue abuse ticket [y/N]: ')
			except: print '\n[!] exiting.'; _exit()
			if not ans.lower() in ['y', 'yes']:
				print '[!] exiting.'
				_exit()

		##################
		## Issue Ticket ##
		##################
		print
		print '[*] Opening ticket'

		#########################
		## Get Department List ##
		#########################
		if not opts.whmcs_deptid:
			opts.whmcs_deptid=display_departmentlist()

		print '[!] Please wait...'
		if not opts.whmcs_proofmsg_fname:
			proofmsg = ''
		else:
			proofmsg = "\n-- CAUSE --\n%s\n""" % opts.whmcs_proofmsg

		# setup template variable replacement
		vars = {
			'cpanel_user': listacct.get('user'),
			'domain_name': listacct.get('domain'),
			'client_name': string.capwords("%s %s" % (clientdetails['firstname'], clientdetails['lastname'])),
			'proof_message': proofmsg
		}
		template  = string.Template(opts.whmcs_ticketmsg)
		ticketmsg = template.safe_substitute(vars)
		
		# invoke api function 
		openticket = whmcs.openticket(clientid=product.get('clientid'), deptid=opts.whmcs_deptid,
									  subject=opts.whmcs_subject, priority="High", message=ticketmsg)
		if openticket == None:
			print '[x] WHMCS openticket API function call failed.'
			print '[!] exiting.'
			_exit()

		result = openticket.get('result')
		if result != 'success':
			print '[!] Unable to issue ticket using clientID (%s) to domain (%s)' % (product1.get('clientid'), listacct1.get('domain'))
			print '[x] %s' % openticket.get('message')
			_exit()

		print '[!] New Ticket (#%s) has been issued.' % openticket.get('tid')

		####################
		## Suspend cPanel ##
		####################
		suspend_cpanel(listacct, openticket)

	end = int(time.strftime('%S'))
	print
	print '[Finished in ~%.1fs]' % abs((end-start))

if __name__ == "__main__": main()
