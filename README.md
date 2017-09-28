Abuse Management Scripts v1.1
=============================
      									
*Version 1.1 release of WHM/WHMCS Abuse Management Scripts contains abuse-manager.py and unsuspend-manager.py.*

**What the script does?**
-------------------
- Suspends/Unsuspends cPanel user account.

- Suspends/Activates the product associated with the domain.

- Generates Open/Reply ticket using ticket template message to specific department.  

**Included Files**
---------------
- abuse-manager.py: *executed by the user with required options.*

- conf/abuse-manager.conf
 - must contain required server, port and login detail of WHM and WHMCS server.
 - accesskey must be set manually on WHMCS configuration.php file.
 - configuration file sample
 		[whm]
		server = https://127.0.0.1
		port = 2087
		username = admin
		password = secret

		[whmcs]
		server = http://127.0.0.1
		port = 80
		username = admin
		password = secret
		accesskey = abc@123

- template/tt.txt
 - sample abuse ticket template file.

- template/rt.txt
 - sample reply ticket template file.

- template/st.txt
 - sample cPanel suspend reason template file.

- template/pt.txt
 - sample proof template file.

- README.md
 - This README file.

**Required Configuration**
====================

Create API admin user and Assign API access role
------------------------------------------
- Use administrative role option from Setup menu
  and create new API access role and assign it to
  API admin user.

- Edit configurtion.php in WHMCS Seirver
 - Edit configuration.php in WHMCS server and update or add $accesskey variable
   at the end of the configuration finle with secret api accesskey value.
   Ex: $api_access_key="secret";

- Edit WHM and WHMCS server configuration file (config/abuse-manager.conf) with server information

- Edit open ticket message and cPanel reason message template with desire abuse template message
 - Custom fields avaiable in opening ticket message template:
  - cPanel Account User:        $cpanel_user
  - Actual Domain Name:         $domain_name
  - WHMCS Client Name:          $client_name

- Custom fields avaiable in reply ticket message template:
  - cPanel Account User:        $cpanel_user
  - Actual Domain Name:         $domain_name
  - WHMCS Client Name:          $client_name

  - Custom fields avaiable in cPanel suspend reason template:
   -  WHMCS Ticket ID:          $ticket_id

**Usage**
-----
 $ python %s [-c config_file] [-s server_name]
   [--search domain|username] ...

**Bugs Reporting**
--------------
- Project Page: http://192.168.3.116/projects/cpscript

**Author**
------
**Purushottam Tuladhar**
