'''
-------------------------------------------------------------------------------
This script is a baseline for multithreaded conversion of all of the scripts.
I'll look into converting the repo to use multithread, some day.
-------------------------------------------------------------------------------
'''

from datetime import datetime
import csv
import logging
from multiprocessing.dummy import Pool as ThreadPool
#from multiprocessing.dummy import cpu_count # Broken as of March 2017 in 3.x
#from netmiko import ConnectHandler
import netmiko
import credentials # Local import of credentials.py


STARTTIME = datetime.now() # Begin timing the script

COMMANDLIST = []
command = ""
#POOL = ThreadPool(cpu_count() - 1) # Missing from lib as of 03/2017
POOL = ThreadPool()

def check_config_mode(config):
    '''Verifies if script is running config changes or not. Redundant.'''
    if config is not None:
        logging.debug("Config Mode Enabled")
        return True
    else:
        logging.debug("Config Mode Disabled")
        return False

def generate_ip_list(custdictionary):
    '''Return a list of IP's from the dictionary'''
    ip_list = [d['IP_Address'] for d in custdictionary if 'IP_Address' in d]
    logging.debug("IP List generated:")
    logging.debug(str(ip_list))
    return ip_list


def generate_cust_dict(customer):
    '''Generates a dictionary from the customer data csv file'''
    with open(customer, mode='r') as csvfile:
        reader = csv.DictReader(csvfile)
        data = []
        for line in reader:
            data.append(line)
        logging.debug("Customer Dictionary:")
        logging.debug(str(data))
        return data


def find_by_ip(lst, value):
    '''Returns the row that a specific IP is in (search for row by IP)'''
    for row in lst:
        if str(row['IP_Address']) == str(value):
            return row


def generate_switch_dict(username, password, secret, matchrow, command):
    '''Makes the switch dictionary for Netmiko's connection handler'''
    swlist = [username, password, secret, matchrow['device_type'], matchrow['IP_Address'], matchrow['SysName'], command]
    logging.debug("Switchlist:")
    logging.debug(str(swlist))
    return swlist


def generate_listof_lists(custdictionary, command, creds):
    '''Returns a list of lists from the input dictionary'''
    swlist = []
    if creds is not None:
        username, password, secret = credentials.cred_csv(creds)
    else:
        username, password, secret = credentials.cred_csv()
    for row in custdictionary:
        swlist.append(generate_switch_dict(username, password, secret, row, command))
    logging.debug("List of Lists:")
    logging.debug(str(swlist))
    return swlist


def switch_run_command(username, password, secret, devicetype, ipaddr, hostname, clicomm):
    '''All the logic happens here. Take the data, process it, print results'''
    sessiondict = {
        'device_type': devicetype,
        'ip': ipaddr,
        'username': username,
        'password': password,
        'secret': secret,
        'verbose': False
        }
    try:
        # Start the session, enable, send the commands, capture terminal output and remove the connections
        session = netmiko.ConnectHandler(**sessiondict)
        session.enable()
        session_return = session.send_command(clicomm)
        session.disconnect()
    except (netmiko.ssh_exception.NetMikoTimeoutException):
        session_return = "----------DEVICE CONNECTION FAILED----------"
    # Fancy formatting here for results
    print("\n\n>>>>>>>>> {0} {1} <<<<<<<<<\n".format(hostname, ipaddr)
          + session_return
          + "\n>>>>>>>>> End <<<<<<<<<\n")
    

def switch_run_config(username, password, secret, devicetype, ipaddr, hostname, clicomm):
    '''All the logic happens here. Take the data, process it, print results'''
    sessiondict = {
        'device_type': devicetype,
        'ip': ipaddr,
        'username': username,
        'password': password,
        'secret': secret,
        'verbose': False
        }
    try:
        # Start the session, enable, send the commands, capture terminal output and remove the connections
        session = netmiko.ConnectHandler(**sessiondict)
        session.enable()
        session_return = session.send_config_set(COMMANDLIST)
        session.disconnect()
    except (netmiko.ssh_exception.NetMikoTimeoutException):
        session_return = "----------DEVICE CONNECTION FAILED----------"
    # Fancy formatting here for results
    print("\n\n>>>>>>>>> {0} {1} <<<<<<<<<\n".format(hostname, ipaddr)
          + session_return
          + "\n>>>>>>>>> End <<<<<<<<<\n")

def info_command(command, csv, db, ip, creds):
    '''This runs a single command against all devices'''
    if csv is not None:
        switchdata = generate_cust_dict(csv) #dictionary of all switch data
        switchlists = generate_listof_lists(switchdata, command, creds)
        results = POOL.starmap(switch_run_command, switchlists)
        POOL.close()
        POOL.join()
    elif db is not None:
        # TODO
        print("SQL functionality is not supported at this time.")
    elif ip is not None:
        # TODO
        print("IP-specific functionality is not supported at this time")
    

def config_command(config, csv, db, ip, creds):
    '''A variable here can be made available to a subprocess...maybe?'''
    if csv is not None:
        switchdata = generate_cust_dict(csv) #dictionary of all switch data
        switchlists = generate_listof_lists(switchdata, command, creds)
        results = POOL.starmap(switch_run_config, switchlists)
        POOL.close()
        POOL.join()
    elif db is not None:
        print("SQL functionality is not supported at this time.")
    elif ip is not None:
        print("IP-specific functionality is not supported at this time")


#RESULTS = POOL.map(switch_run_command, IP_LIST)

#POOL.close()
#POOL.join()

ENDTIME = datetime.now()
TOTALTIME = ENDTIME - STARTTIME
