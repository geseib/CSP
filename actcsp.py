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
my_csp_host="10.1.10.108"
my_csp_user="admin"
my_csp_password="admin"

#Images to use - Change these as needed
my_CSR_image="csr1000v-universalk9.03.16.00.S.155-3.S-ext.iso"
my_NXOS_image="nxosv-final.7.0.3.I2.1.qcow2"
my_XR_image="iosxrv-k9-demo-5.1.2.qcow2"
my_LINUX_image="ubuntu-14.04-server-cloudimg-amd64-disk1.qcow2"

#VNIC PROFILE  -not working at the moment
profile =[('trunk',1, 'internal1'),('trunk',1, 'internal2'),('access',100, 'eno1')]

#Setup what arguments are expected and supported
usage = "usage: %prog [options]"
parser= OptionParser(usage=usage)
parser.add_option("-s","--server", dest="acsp", help="IP address/hostname of the of the CSP", default=my_csp_host)
parser.add_option("-U","--user", dest="auser", help="User for the of the CSP", default=my_csp_user)
parser.add_option("-P","--password", dest="apass", help="password for the of the CSP", default=my_csp_password)

parser.add_option("-u","--up", dest="aup", help="bring up routers, use name or use 'ALL'")
parser.add_option("-d","--down", dest="adown", help="bring down  routers, use name or use 'ALL'")

parser.add_option("-D","--delete", dest="adelete", help="This deletes routers, use name or use 'ALL'")
parser.add_option("-l","--list", action="store_true", dest="alist", help="list services on this CSP")
parser.add_option("-t","--type", dest="atype", help="pick type of service to deploy: CSR XR,or NXOS, default is %default", default="CSR")
parser.add_option("-c","--create", dest="acreate", help="create new service with given name")
parser.add_option("-n","--number", dest="anumber", help="Number of copies of service to create. appends to name used for -c")
parser.add_option("-S","--status", action='store_true', dest="astatus", help="General Info on the CSP-2100 Server")


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
        for each in jlists['services']['service']:
            plist.append(each['name'])

#Check the power up status of the service
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

#Display info about resources
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
    
#Display the List of services on the CSP and the power status
def list_services():
    show_resources()
    print "\n"
    print "SERVICE NAME    -> POWER ON/OFF"
    print "==============================="
    for each in plist:
        if len(each)< 8:
            print str(each)+"\t\t->\t"+get_service_status(each)
        else:
            print str(each)+"\t->\t"+get_service_status(each)
    print "\n"+str(len(plist)) +" Services currently listed"
    show_resources()
        
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
#Change memory, CPU count, and iso depnding on the OS to load to configure a new service
def get_service_profile ():
    profile=options.atype
    if profile.upper()=='CSR':
        iso=my_CSR_image
        memory=int(2048)
        cpus=int(1)
        return (iso,memory,cpus)
    elif profile.upper()=='NXOS':
        iso=my_NXOS_image
        memory=int(4096)
        cpus=int(1)
        return (iso,memory,cpus)
    elif profile.upper()=='XR':
        iso=my_XR_image
        memory=int(4096)
        cpus=int(1)
        return (iso,memory,cpus)
    elif profile.upper()=='LINUX':
        iso=my_LINUX_image
        memory=int(4096)
        cpus=int(1)
        return (iso,memory,cpus)
    
    else:
        print "Unkown image type, NOTHING Created"
        exit()
#
#Adjust the VNIC configuration. This does not work
def set_vnic():
    nic=0
    chunk={}
    for each in profile:
        if each[0]=='trunk':
            chunk.append('"nic": '+str(nic)+',"type":"'+each[0]+'","tagged":"true","native":"'+str(each[1])+'","network_name":"'+each[2]+'"},')
        elif each[0]=='access':
            chunk.append('{"nic": '+str(nic)+',"type":"'+each[0]+'","tagged":"true","vlan":"'+str(each[1])+'","network_name":"'+each[2]+'"},')
        nic+=1
    vnic ={"vnic": chunk}
    

    return vnic
        
        
#Create a new service
def create_service(service):
    if service not in plist:
        csp_service_url="https://"+csp_host+"/api/running/services"
        iso,memory,cpus=get_service_profile()
        internal2=str(options.acreate)
        payload = {"service": {"disk_size": 4, "name": service, "power": "on", "iso_name": iso, "numcpu": cpus, "macid": 1, "memory": memory, "vnics": {"vnic": [{"nic": 0,"type":"access","tagged":"false","vlan":"1","network_name":"eno1"}, {"nic": 1,"type":"trunk","tagged":"true","native":"1","network_name": internal2}, {"nic": 2,"type":"trunk","tagged":"true","native":"1","network_name":"Internal1"}]},}}
        #print payload
        #vnic=set_vnic()
        #print vnic
        #payload = {"service": {"disk_size": 4, "name": service, "power": "on", "iso_name": iso, "numcpu": cpus, "macid": 1, "memory": memory, "vnics": vnic,}}
        #print payload
        print "Creating Service: "+str(service)
        create = requests.post(csp_service_url, auth=HTTPBasicAuth(csp_user, csp_password), verify=False, json=payload, headers={'Content-type': 'application/vnd.yang.data+json'})
        print "Service "+service+" is now powered "+ str(get_service_status(service))+"\r\n"
        return
    else:
        print "Service "+service+" already exists, NOTHING Created"
        return
#Delete a service    
def delete_service (service):
    print "deleting "+str(service)
    payload = {"service": {"power": "off", }}
    csp_service_url="https://"+csp_host+"/api/running/services/service/"+str(service)    
    downing=requests.patch(csp_service_url, auth=HTTPBasicAuth(csp_user, csp_password), verify=False, json=payload, headers={'Content-type': 'application/vnd.yang.data+json'})
    sleep(2)
    deleting=requests.delete(csp_service_url, auth=HTTPBasicAuth(csp_user, csp_password), verify=False, json=payload, headers={'Content-type': 'application/vnd.yang.data+json'})
    print "DONE\n"
    return


#START OF APP
print"=========================="
print"|     ACTCSP - 2015       |"
print"=========================="
print"\n"

#get a list of current services on CSP and store in variable plist
get_services()

if options.alist:
    list_services()
    print "\n"

#CHECK FOR DOWN ARG and if single, multiple (i.e. router1,router2,router3 using the -n arg), or ALL
if options.aup:
    service=options.aup
    if service.upper() == "ALL":
        for each in plist:
            up_service(each)
    elif service in plist:
        up_service(service)
    elif service not in plist:
        print "Cannot find service " +str(service)
        print " NO ACTION TAKEN"
#CHECK FOR DOWN ARG and if single, multiple (i.e. router1,router2,router3 using the -n arg), or ALL
if options.adown:
    service=options.adown
    if service.upper() == "ALL":
        for each in plist:
            down_service(each)
    elif options.anumber:
            totalservices=int(options.anumber)
            servicenumber = 1
            while servicenumber < totalservices+1:
                if str(service)+str(servicenumber) in plist:
                    down_service(str(service)+str(servicenumber))
                
                else:
                    print "No service "+str(service)+str(servicenumber)+" to bring down."
                servicenumber += 1
    elif service in plist:
        down_service(service)
    elif service not in plist:
        print "Cannot find service " +str(service)
        print " NO ACTION TAKEN"

#CHECK FOR DELETE ARG and if single, multiple (i.e. router1,router2,router3 using the -n arg), or ALL
if options.adelete:
    service=options.adelete
    check_confirmation=raw_input("Are you sure you want to delete "+service+" (CANNOT BE REVERSED)? type 'CONFIRM' in upper case: ")
    if check_confirmation=="CONFIRM":
        if service.upper() == "ALL":
            for each in plist:
                delete_service(each)
        elif options.anumber:
            totalservices=int(options.anumber)
            servicenumber = 1
            while servicenumber < totalservices+1:
                if str(service)+str(servicenumber) in plist:
                    delete_service(str(options.adelete)+str(servicenumber))
                else:
                    print "No service "+str(service)+str(servicenumber)+" to bring delete."
                servicenumber += 1
        elif service in plist:
            delete_service(service)
        elif service not in plist:
            print "Cannot find service " +str(service)
            print " NO ACTION TAKEN"
    else:
        print ("Nothing Deleted. That was close!")
        
#CHECK FOR CREATE ARG and if single, multiple (i.e. router1,router2,router3 using the -n arg)   
if options.acreate:                
    if options.anumber:
        totalservices=int(options.anumber)
        servicenumber = 1
        while servicenumber < totalservices+1:
            create_service(str(options.acreate)+str(servicenumber))
            servicenumber += 1
    else:
        create_service(str(options.acreate))
#General Server Info
if options.astatus:
    show_resources()
    
