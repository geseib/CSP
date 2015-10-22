# actcsp.py by George Seib, Cisco Systems
# multifunction tool for the Cisco CSP 2100
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
my_csp_host="10.90.16.74"
my_csp_user="admin"
my_csp_password="admin"
plist=[]

#Setup what arguments are expected and supported
usage = "usage: %prog [options]"
parser= OptionParser(usage=usage)
parser.add_option("-s","--server", dest="acsp", help="IP address/hostname of the of the CSP", default=my_csp_host)
parser.add_option("-U","--user", dest="auser", help="User for the of the CSP", default=my_csp_user)
parser.add_option("-P","--password", dest="apass", help="password for the of the CSP", default=my_csp_password)


(options, args) = parser.parse_args()

#Global Variables: DO NOT CHANGE THESE
csp_host = options.acsp     #This is the CSP server address, pulled from parser section above or the --server arg
plist=[]                    #This is where the list of Service will be stored
csp_user = options.auser
csp_password = options.apass


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
        for each in jlists['services']['service']:
            plist.append(each['name'])

#Check the power up status of the service def
def get_service_status(service):
    local=[]
    csp_service_url="https://"+csp_host+"/api/running/services/service/"+str(service)
    status=requests.get(csp_service_url, auth=HTTPBasicAuth(csp_user, csp_password), verify=False)
    if status.status_code == 401:
        print "Invalid Login Credentials to CSP - Exiting"
        sys.exit(1)
    jstatus=json.loads(status.text)
    local= jstatus['service']['power']
    return (local)


#Display the List of services on the CSP and the power status
def list_services():
    show_resources()
    print "\n"
    print "SERVICE NAME    -> POWER ON/OFF    Console Acces"
    print "====================================================="
    for each in plist:
        if len(each)< 8:
            print str(each)+"\t\t->\t"+get_service_status(each)+"\t"+"Serial"+str(0)+" @ "+csp_host+":"+str(return_serial(each))
        else:
            print str(each)+"\t->\t"+get_service_status(each)+"\t"+"Serial"+str(0)+" @ "+csp_host+":"+str(return_serial(each))
    print "\n"+str(len(plist)) +" Services currently listed"
    show_resources()
  
def show_resources():
    csp_service_url="https://"+csp_host+"/api/running/resources/resource/csp-2100"    
    status=requests.get(csp_service_url, auth=HTTPBasicAuth(csp_user, csp_password), verify=False)
    jstatus=json.loads(status.text)
    server_ip=jstatus['resource']['ip_address']
    hostname=jstatus['resource']['host_name']
    memory_total=jstatus['resource']['ram_total_mb']
    memory_avail=jstatus['resource']['ram_total_mb']-jstatus['resource']['ram_used_mb']
    cpus_total=jstatus['resource']['num_cpus_total']
    cpus_avail=jstatus['resource']['num_cpus_total']-jstatus['resource']['num_cpus_used']
    total_services=jstatus['resource']['num_service']
    print "Server: "+hostname+" @ "+server_ip
    print "=================================="
    print "Memory Total: "+str(memory_total)+"MB\tMemory Free: "+str(memory_avail)+"MB"
    print "Cores Total: "+str(cpus_total)+"\tCores Free: "+str(cpus_avail)
    print str(total_services) +" Services currently configured"

def return_serial(service):
    csp_service_url="https://"+csp_host+"/api/running/services/service/"+str(service)+"/serial_ports/serial_port/"+str(0)    
    status=requests.get(csp_service_url, auth=HTTPBasicAuth(csp_user, csp_password), verify=False)
    try:
        jstatus=json.loads(status.text)
    except:
        return 0
    serial_address=jstatus['serial_port']['service_port']
    return serial_address      

#get a list of current services on CSP and store in variable plist
get_services()

list_services()
print "\n"

