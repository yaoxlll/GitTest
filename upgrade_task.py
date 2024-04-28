from logInit import TimezoneRotatingFileHandler
import logging, json
import re, socket, pathlib
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import settings, util
# import v.device_password as device_password


logger = logging.getLogger('upgradetask')
logger.setLevel(settings.LOG['level'])
filename = settings.LOG['path'] + "upgradetask.log"
max_bytes = settings.LOG['max_bytes']
backup_count = settings.LOG['backup_count']
fh = TimezoneRotatingFileHandler(filename=filename, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s') 
fh.setFormatter(formatter)
logger.addHandler(fh)


def ssh_copy(ip, port, user, password, src, dest):
    socket.setdefaulttimeout(5)
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.connect((ip, port))
    except Exception as e:
        s.close()
        raise

    try:
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.connect(hostname=ip, sock=s, port=port, username=user, password=password, timeout=5)

        with SCPClient(ssh.get_transport()) as scp1:
            scp1.put(src, dest)
    finally:
        ssh.close()

    logger.debug(f"{ip}: copy {src} to {dest} success")


def upgrade_fiwmware(ip, port, user, password, sw_type, os_version, firmware: dict):
    logger.debug(f'{ip}({sw_type}) start upgrade firmware...')

    if os_version == '9.99.999':
        logger.debug(f'{ip}({os_version}) single board test, do not upgrade')
        return
    
    if sw_type not in firmware.keys():
        logger.debug(f'{ip}({sw_type}) swtype not in firmware config')
        return 
    
    version_list: List[dict] = firmware[sw_type]

    for config in version_list:
        if 'ALL' not in config['include'] and ip not in config['include']:
            logger.warning(f"{ip}({sw_type}) dose not include this version({config['version']})")
            continue

        if ip in config['exclude']:
            logger.warning(f"{ip}({sw_type}) is in exclude this version({config['version']})")
            continue

        if config['version'] == os_version:
            logger.debug(f"{ip}({sw_type}) is the same version {config['version']}")
            break

        logger.debug(f"start upgrade {ip}({sw_type}) {os_version} with version {config['version']}")

        firmware_file = f"{settings.FIRMWARE_PATH}{sw_type}/{config['version']}/{config['file_name']}"
        if not pathlib.Path(firmware_file).exists():
            logger.error(f"{firmware_file} done not exist for {ip}({sw_type}, {config['version']})")
            break

        fs_error = call_ssh(ip, port, user, password, "dmesg | grep SQUASHFS")
        if len(fs_error) != 0:
            logger.error("%s file system error: %s(%s, %s)", fs_error, ip, sw_type, config['version'])
            call_ssh(ip, port, user, password, "reboot")
            break

        ssh_copy(ip, port, user, password, firmware_file, '/tmp/firmware.bin')

        sha256sum = call_ssh(ip, port, user, password, 'sha256sum /tmp/firmware.bin')
        if sha256sum.strip() != f"{config['sha256sum']}  /tmp/firmware.bin":
            logger.error(f"{ip}({sw_type}, {config['version']}) copy firmware file({firmware_file}) fail")
            break

        logger.debug(f"{ip}({sw_type}, {config['version']}) copy firmware file({firmware_file}) success")

        call_ssh(ip, port, user, password, "/sbin/sysupgrade -n /tmp/firmware.bin")
        
        logger.debug(f"end upgrade {ip}({sw_type}) {os_version} to new version: {config['version']}")

        break

    logger.debug("%s(%s): end update firmware", ip, os_version)



def get_dev_info(ip, port, user, password):
    logger.debug(f'start get dev info: {ip}...')

    release = call_ssh(ip, port, user, password, 'cat /etc/openwrt_release')

    m1 = re.search("DISTRIB_SYSTEMVER\\s*=\\s*'(.*?)'", release)
    sv_list = m1.group(1).split('-')
    v1 = sv_list[0].replace('v', '')
    v1_list = v1.split('.')

    m2 = re.search("DISTRIB_MINERVER\\s*=\\s*'(.*?)'", release)
    mv_list = m2.group(1).split('-')
    v2 = mv_list[0].replace('v', '')
    v2_list = v2.split('.')

    os_version = v1_list[0] + '.' + v1_list[1] + v1_list[2] + '.' + ('' if v2_list[0]=='0' else v2_list[0]) + v2_list[1] + v2_list[2]

    logger.debug('end get dev info: %s', ip)

    return os_version


def call_ssh(ip, port, user, password, cmd):
    socket.setdefaulttimeout(5)
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.connect((ip, port))
    except Exception as e:
        s.close()
        raise

    try:
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.connect(hostname=ip, sock=s, port=port, username=user, password=password, timeout=5)
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=20)
        #r = stdout.readlines()
        r1 = stdout.read().decode()
        r2 = stderr.read().decode()

        if len(r1) != 0:
            logger.debug('%s stdout for %s: %s', ip, cmd, r1)
            return r1
        else:
            logger.debug('%s stderr for %s: %s', ip, cmd, r2)
            return r2
    finally:
        ssh.close()


def get_hwinfo(ip):
    try:
        url = f"http://{ip}/cgi-bin/luci/admin/ipollo_main/ipollo_devinfo"
        resp = requests.get(url, timeout=2).json()
        logger.debug(f'hwinfo for {ip} is {resp}')

        return resp
    except:
        logger.exception(f'Exception occured when get hwinfo ({ip})')
        
        return {}


def upgrade_device(ip, port, default_user, default_password, firmware):
    logger.debug(f'start upgrade device({ip})...')

    try:
        hwinfo_dict = get_hwinfo(ip)
        miner_sn = hwinfo_dict['SN']
        model = hwinfo_dict['Model']
        hw_type =hwinfo_dict['HwType']
        sw_type = hwinfo_dict['SwType']

        user = default_user
        password = default_password

        if model in settings.DEVICE_MODEL_ESA:
            try:
                serial = hwinfo_dict['Serial']
                board = hwinfo_dict['Board']
                project_ver = hwinfo_dict['Project']

                if project_ver == settings.DEVICE_INFO['project']:
                    cbsn = hwinfo_dict['SN']

                    if board == settings.DEVICE_INFO['board']:
                        cbsn = ''
                    
                    # password = device_password.testlib(cbsn, serial)
                    if password is None:
                        logger.info(f"get_device_password failed, ip({ip}, cbsn({cbsn}), cpuid({serial}))")
            except:
                logger.exception(f'exception occured, no cpuid board project_ver in devinfo: {ip}')

        try:
            call_ssh(ip, port, user, password, 'ls /')
        except:
            logger.exception(f'{ip}({miner_sn}) exception occured in password: {password}')
            raise

        os_version = get_dev_info(ip, port, user, password)

        try:
            upgrade_fiwmware(ip, port, user, password, sw_type, os_version, firmware)
        except:
            logger.exception(f'{ip}({miner_sn}) exception occured when upgrade firmware')
            raise

        logger.debug(f'end upgrade device({ip}).')

        return True
    
    except:
        logger.exception(f'Exception occured when upgrade device ({ip})')


def get_firmware_data():
    logger.debug('start get firmware from bench web platform...')

    api_url = f"{settings.PLATFORM['url']}{settings.PLATFORM['firmware_data']}"

    resp = requests.get(api_url, timeout=3).json()

    if resp['code'] == 0:
        logger.debug(f'firmware response from bench platform: {resp}')

        firmware = util.gen_firmware(resp['data'])
        logger.debug(f'generated firmware dict: {firmware}')

        return firmware

    else:
        raise resp['message']


def get_device_ips():
    logger.debug('start get device ips...')

    api_url = f"{settings.PLATFORM['url']}{settings.PLATFORM['bench_device_ip']}"

    resp = requests.get(api_url, timeout=3).json()

    if resp['code'] == 0:
        logger.debug(f"End device ips: {resp['data']}")

        return resp['data']
    
    else:
        raise resp['message']


def scan():
    logger.debug('start upgrade...')

    default_user = settings.DEVICE['user']
    default_password = settings.DEVICE['password']
    port = settings.DEVICE['port']

    try:
        ips = get_device_ips()
    except:
        logger.exception(f'Exception occured when get device ips')
        return
    
    try:
        firmware = get_firmware_data()
    except:
        logger.exception('Exception occured when get firmware from platform')
        return

    pool = ThreadPoolExecutor(200)
    [pool.submit(upgrade_device, ip, port, default_user, default_password, firmware) for ip in ips]
    pool.shutdown(wait=True)

    logger.debug('end upgrade.')

if __name__ == '__main__':
    scan()



