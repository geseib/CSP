# CSP
python scripts to automate common task on the Cisco Cloud serivces Platform

listcsp.py lists services and config info about a service

modcsp.py allows changing the TCP port used for Serial over TCP for a service

pniccsp lists the physical NICs in the CSP server

actcsp.py is the swiss army knife script


some thing syou can do
up.down a service or all serivices
list services
list info on a service
create a service
delete a service or all services

some examples for actcsp

#list the current services on the CSP
actcsp.py -l

#down a service named 'CSR1'
actcsp.py -d CSR1

#down all services
actcsp.py -d ALL

#down all sequential named services 'CSR1'-'CSR10'
actcsp.py -d CSR -n 10

#down all sequential named services 'myXR1'-'myXR4'
actcsp.py -d myXR -n 4

#bring up a service named 'CSR1'
actcsp.py -u CSR1

#create 10 services 'CSR1'-'CSR10'
actcsp.py -c CSR -n 10

#delete a service named 'CSR1'
actcsp.py -D CSR1

#delete all services
actcsp.py -D ALL

#delete all sequential services 'myXR1'-'my-XR4'
actcsp.py -D myXR -n4

#override the script default CSP server address to '10.1.1.1' and list services
actcsp.py -l -server 10.1.1.1

#override the script default login to 'user' with password 'easyguess' and create service 'CSR1'
actcsp.py -c CSR1 -U user -P easyguess

