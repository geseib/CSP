# actcsp.py by George Seib, Cisco Systems
# Change Serial TCP port tool for the Cisco CSP 2100
#

#requires requests to connect to the CSP using https
#install using 'pip install requests
from requests.auth import HTTPBasicAuth
import requests
import json
import sys
import logging
from time import sleep
#setup logging
logging.captureWarnings(True)

#requires optparse to get arguments from command line
#nothing to unstall with python 2.7
from optparse import OptionParser

#GLOBAL CSP Server VARIABLES. CHANGE THESE AS NEEDED
my_csp_host="10.1.10.108"
my_csp_user="admin"
my_csp_password="admin"

#Setup what arguments are expected and supported
usage = "usage: %prog [options]"
parser= OptionParser(usage=usage)
parser.add_option("-s","--server", dest="acsp", help="IP address/hostname of the of the CSP", default=my_csp_host)
parser.add_option("-U","--user", dest="auser", help="User for the of the CSP", default=my_csp_user)
parser.add_option("-P","--password", dest="apass", help="password for the of the CSP", default=my_csp_password)

parser.add_option("-m","--modify", dest="amodify", help="Modify a Service followed by the Service name")
parser.add_option("--port", dest="aport", help="New Serial TCP Port")

parser.add_option("-S","--status", dest="astatus", help="General Info on the CSP-2100 Server, name of service or use CSP for server")
parser.add_option("-v","--debug", action="store_true", dest="adebug", help="verbose dubuging")

(options, args) = parser.parse_args()

#Global Variables: DO NOT CHANGE THESE
csp_host = options.acsp     #This is the CSP server address, pulled from parser section above or the --server arg
plist=[]                    #This is where the list of Service will be stored
csp_user = options.auser
csp_password = options.apass

#retrieve the list services that exist on the CSP server
def get_services():
    csp_service_url="https://"+csp_host+"/api/running/services"
    try:
        lists=requests.get(csp_service_url, auth=HTTPBasicAuth('admin','admin'), verify=False)
    except requests.ConnectionError, e:
        print "Cannot connect to server "+str(csp_host)+", Exiting"
        sys.exit(1)
        
    if lists.text == "":
        print "No Services on the CSP"
        print "\n"
    else:    
        
        jlists=json.loads(lists.text)
        global plist
        plist=[]
        for each in jlists['services']['service']:
            plist.append(each['name'])

def show_serial(service,port):
    csp_service_url="https://"+csp_host+"/api/running/services/service/"+str(service)+"/serial_ports/serial_port/"+str(port)    
    status=requests.get(csp_service_url, auth=HTTPBasicAuth(csp_user, csp_password), verify=False)
    jstatus=json.loads(status.text)
    print jstatus
    print "Serial"+str(port)+" @ "+csp_host+":"+str(jstatus['serial_port']['service_port'])

def return_serial(service):
    csp_service_url="https://"+csp_host+"/api/running/services/service/"+str(service)+"/serial_ports/serial_port/"+str(0)    
    status=requests.get(csp_service_url, auth=HTTPBasicAuth(csp_user, csp_password), verify=False)
    try:
        jstatus=json.loads(status.text)
    except:
        
        return 0
    serial_address=jstatus['serial_port']['service_port']
    return serial_address
#power up a service        
def up_service(service):
    print "bringing up service "+str(service)
    payload = {"service": {"power": "on", }}
    csp_service_url="https://"+csp_host+"/api/running/services/service/"+str(service)    
    upping=requests.patch(csp_service_url, auth=HTTPBasicAuth(csp_user, csp_password), verify=False, json=payload, headers={'Content-type': 'application/vnd.yang.data+json'})
    print "DONE \n"
#Power down a service
def down_service(service):
    print "bringing down service "+str(service)
    payload = {"service": {"power": "off", }}
    csp_service_url="https://"+csp_host+"/api/running/services/service/"+str(service)    
    downing=requests.patch(csp_service_url, auth=HTTPBasicAuth(csp_user, csp_password), verify=False, json=payload, headers={'Content-type': 'application/vnd.yang.data+json'})
    print "DONE \n"


def modify_serial(service):
    print "changing serial port from "+str(return_serial(service))+" to "+str(options.aport)
    payload = {"service": {"serial_ports":{"serial_port":[{"serial": 0,"serial_type":"telnet","service_port":options.aport}]},}}
    csp_service_url="https://"+csp_host+"/api/running/services/service/"+str(service)    
    upping=requests.patch(csp_service_url, auth=HTTPBasicAuth(csp_user, csp_password), verify=False, json=payload, headers={'Content-type': 'application/vnd.yang.data+json'})
    print "DONE \n"

def verify_free_port():
    for each in plist:
        if options.adebug:
            print str(options.aport) +" comparing with "+each+":"+ str(return_serial(each))
        
        if str(options.aport) == str(return_serial(each)):
            print "Cannot use port "+options.aport+" it's in use by "+each
            sys.exit(1)
            
    else:
        return
        

get_services()
if options.adebug:
    print "Verbose Debuging on"

if options.amodify and options.amodify in plist:
    print "Found Service "+options.amodify
    
    while True:
        verify_ok=raw_input("This will down the service before modifying, and then bring back up. Ok? (yes/no):")
        if verify_ok.upper() not in ("NO","YES","N","Y"):
            print " Not a valid response. Must be Yes or No"
        else:
            break
        
    if verify_ok.upper() =="NO" or verify_ok.upper() =="N":
        print "ok, Cancelling"
        sys.exit(1)
    elif verify_ok.upper() =="YES" or "Y":
        if options.aport:
            verify_free_port()
            print "Changing the Serial TCP Port to "+str(options.aport)
            down_service(options.amodify)
            modify_serial(options.amodify)
            up_service(options.amodify)
            
            
        
