from concurrent.futures import ThreadPoolExecutor, as_completed
from logInit import TimezoneRotatingFileHandler
import socket
import logging
import re

from paramiko import SSHClient, AutoAddPolicy

import settings


logger = logging.getLogger('apipsu')
logger.setLevel(settings.LOG['level'])
filename = settings.LOG['path'] + "apipsu.log"
max_bytes = settings.LOG['max_bytes']
backup_count = settings.LOG['backup_count']
fh = TimezoneRotatingFileHandler(filename=filename, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s') 
fh.setFormatter(formatter)
logger.addHandler(fh)


def get_power():
    logger.debug('start get power from ssh...')

    power_ip = settings.PSU['power_ip']
    port = settings.PSU['port']
    username = settings.PSU['username']
    password = settings.PSU['password']

    pool = ThreadPoolExecutor(20)
    power_task = [pool.submit(call_ssh, ip, port, username, password, 'psu -P') for ip in power_ip]

    result = {}
    for task in as_completed(power_task):
        lines = task.result()
        logger.debug('psu -P is: %s', lines)
        psu = {}

        for line in lines:
            m = re.search(r"IP:(.*?) ID:(.*?) Volt:(.*?)\(V\) Current:(.*?)\(A\) AP:(.*?)\(KW\)", line)
            ip = m.group(1)
            iid = m.group(2)
            volt = m.group(3)
            current = m.group(4)
            ap = m.group(5)
            psu[ip] = {'id': iid, 'v': volt, 'i': current, 'ap': ap}

        result.update(psu)

    logger.debug('psu -P return: %s', result)
    return result


def get_temperature():
    logger.debug('start get temperation...')

    temp_ip = settings.PSU['temp_ip']
    port = settings.PSU['port']
    username = settings.PSU['username']
    password = settings.PSU['password']

    lines = call_ssh(temp_ip, port, username, password, "psu -T")
    logger.debug(f'temperature is: {lines}')

    temp = {}
    humis = []
    temps = []
    
    for line in lines:
        m = re.search(r"humidity:(.*?)\(%RH\) Temperature:(.*?)\(℃\)", line)
        humis.append(m.group(1))
        temps.append(m.group(2))

    temp['humi'] = max(humis)
    temp['temp'] = max(temps)
    logger.debug('psu -T return: %s', temp)
    return temp


def call_ssh(ip, port, username, password, cmd):
    socket.setdefaulttimeout(5)

    s =socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.connect((ip, port))
    except Exception as e:
        s.close()
        raise

    try:
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.connect(hostname=ip, sock=s, port=port, username=username, password=password, timeout=5)
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=20)
        r = stdout.readlines()
        #r = stdout.read().decode()
        logger.debug('stdout for %s: %s', cmd, r)
        return r
    except:
        logger.exception(f'Exception occured when call ssh, cmd: {cmd}')
    finally:
        ssh.close()
