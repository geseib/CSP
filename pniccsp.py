# pniccsp.py by George Seib, Cisco Systems
# pysical NIC listing for the Cisco CSP 2100
#

#requires requests to connect to the CSP using https
#install using 'pip install requests
from requests.auth import HTTPBasicAuth
import requests
import json
import sys
import logging
from time import sleep

#requires optparse to get arguments from command line
#nothing to install with python 2.7
from optparse import OptionParser

#GLOBAL CSP Server VARIABLES. CHANGE THESE AS NEEDED
my_csp_host="10.1.10.108"
my_csp_user="admin"
my_csp_password="admin"
#setup logging  as Warning will appear if you use a self signed certificate on server
logging.captureWarnings(True)

#Setup what arguments are expected and supported
usage = "usage: %prog [options]"
parser= OptionParser(usage=usage)
parser.add_option("-s","--server", dest="acsp", help="IP address/hostname of the of the CSP", default=my_csp_host)
parser.add_option("-U","--user", dest="auser", help="User for the of the CSP", default=my_csp_user)
parser.add_option("-P","--password", dest="apass", help="password for the of the CSP", default=my_csp_password)


parser.add_option("-d","--detail", action="store_true", dest="adetails", help="get details on each PNIC")
parser.add_option("-v","--debug", action="store_true", dest="adebug", help="verbose dubuging")

(options, args) = parser.parse_args()

#Global Variables: DO NOT CHANGE THESE
csp_host = options.acsp     #This is the CSP server address, pulled from parser section above or the --server arg
plist=[]                    #This is where the list of Service will be stored
csp_user = options.auser
csp_password = options.apass



def get_pnics():
    csp_service_url="https://"+csp_host+"/api/running/pnics"
    try:
        lists=requests.get(csp_service_url, auth=HTTPBasicAuth('admin','admin'), verify=False)
    except requests.ConnectionError, e:
        print "Cannot connect to server "+str(csp_host)+", Exiting"
        sys.exit(1)

    if lists.text == "":
        print "No PNICs on the CSP"
        print "\n"
    else:

        jlists=json.loads(lists.text)
        global plist
        plist=[]
        for each in jlists['pnics']['pnic']:
            plist.append(each['name'])

def list_pnics():
    print "\nPhysical NICS in"+ csp_host
    print "============================"
    for each in plist:
        print str(each)
    print"\n"+str(len(plist))+" NICs Total"



#Check the power up status of the service def
def get_pnic_details(pnic):
    local=[]
    csp_service_url="https://"+csp_host+"/api/running/pnics/pnic/"+str(pnic)
    status=requests.get(csp_service_url, auth=HTTPBasicAuth(csp_user, csp_password), verify=False)
    if status.status_code == 401:
        print "Invalid Login Credentials to CSP - Exiting"
        sys.exit(1)
    jstatus=json.loads(status.text)
    print "\nConfig for PNIC: "+pnic
    print "==============================="
    for each in jstatus['pnic']:
        if str(each)=="serial_ports":
            get_serials(service)
        elif str(each)=="vnics":
            get_vnics(service)
        elif len(each)<7:
            print str(each)+"\t\t"+str(jstatus['pnic'][str(each)])
        else:
            print str(each)+"\t"+str(jstatus['pnic'][str(each)])


get_pnics()
list_pnics()

if options.adetails:
    for each in plist:
        get_pnic_details(each)
