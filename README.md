# README #

Will deploy a pythonscript in a raspberry pi an set it up as a persistant service (start after reboot)

Configuration is done L313 to L319 in deployer.py (script to deploy, service name, raspberry ip)

### requirements ###

*** on your computer : ***

* pip install docopt
* pip install paramiko

*** on the raspberry : ***

* sudo apt-get install python-pip
* pip install RPi.GPIO

### ledflasher.py ###

This is an example, it will flashes 3 led again and again and again on GPIO 16-20-21

### The deployers ###

* can deploy (purge the folder containing the script)
* can update (overwrite only the script) even if the service is already running
* setup a service that can be started/stopped and is lauched at startup vis systemd

### deployer configuration and usage ###

* configure your ssh root login/mdp and raspberry ip in deployer.py 
* to deploy the first time : `python deployer.py install`, service is now running
* to re-deploy while the service is already running : `python deployer.py redeploy` (upload code, restart service, do not other file in directory)

### how to use the systemd service ###

* `systemctl status <service_name>` to know what is going on
* `systemctl restart <service_name>` to restart it (same as doing stop then start)
* `systemctl start <service_name>` to start it
* `systemctl stop <service_name>` to stop it
* `journalctl -u <service_name>` to view the logs

### TIPS ###

* reboot pi : `sudo shutdown -r now`
* shutdown pi : `sudo shutdown -h now`
* ssh conf menu (activate camera, etc) : `sudo raspi-config`