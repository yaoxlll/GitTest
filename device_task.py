import logging
from logInit import TimezoneRotatingFileHandler
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

import settings
import util


logger = logging.getLogger('devicetask')
logger.setLevel(settings.LOG['level'])
filename = settings.LOG['path'] + 'devicetask.log'
max_bytes = settings.LOG['max_bytes']
backup_count = settings.LOG['backup_count']
fh = TimezoneRotatingFileHandler(filename=filename, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)


def handle_device(new_sn_list_v, new_data_list_v, new_sn_list_k, new_data_list_k):
    logger.debug('start handle device...')

    api_url_v = f"{settings.PLATFORM['url']}{settings.PLATFORM['handle_device_v']}"
    resp_v = requests.post(url=api_url_v, timeout=40, json={'sn': new_sn_list_v, 'data': new_data_list_v}).json()

    api_url_k = f"{settings.PLATFORM['url']}{settings.PLATFORM['handle_device_k']}"
    resp_k = requests.post(url=api_url_k, timeout=40, json={'sn': new_sn_list_k, 'data': new_data_list_k}).json()

    if resp_v['code'] == 0 and resp_k['code'] == 0:
        logger.debug('end handle device.')
    
    else:
        raise resp_v['message'] + resp_k['message']


def get_hwinfo(ip):
    try:
        url = f"http://{ip}/cgi-bin/luci/admin/ipollo_main/ipollo_devinfo"
        resp = requests.get(url, timeout=5).json()
        logger.debug(f'hwinfo for {ip} is {resp}')

        return resp
    except Exception as e:
        logger.warning(f'{ip} exception occured when get hwinfo({e})')
        
        return None


def get_info(ip):
    logger.debug(f'start get_info {ip}...')

    try:
        hwinfo_dict = get_hwinfo(ip)

        if hwinfo_dict is None:
            return None

        v = {}
        v['miner_sn'] = hwinfo_dict['SN']
        v['model'] = hwinfo_dict['Model']
        v['hw_type'] = hwinfo_dict['HwType']
        v['sw_type'] = hwinfo_dict['SwType']
        v['scan_ip'] = ip
        v['os_version'] = 'unknown'

        # v
        device_hw_type = settings.DEVICE_HWTYPE_V
        if len(device_hw_type) != 0:
            if v['hw_type'] in device_hw_type:
               logger.debug(f'end get_info {ip}.')
               return "v", v
        
        # k
        device_hw_type = settings.DEVICE_HWTYPE_K
        if len(device_hw_type) != 0:
            if v['hw_type'] in device_hw_type:
               logger.debug(f'end get_info {ip}.')
               return "k", v 

        logger.debug(f"{ip}({v['hw_type']}) not in config hwtype")
        return None
    
    except:
        logger.exception(f'Exception occured when get info ({ip})')
        return None


def get_ips():
    logger.debug('start get ips from bench web platform...')

    api_url = f"{settings.PLATFORM['url']}{settings.PLATFORM['get_ips']}"

    resp = requests.get(url=api_url, timeout=3).json()

    if resp['code'] == 0:
        logger.debug(f'ip resp from bench web platform: {resp}')

        ips = util.gen_ip(resp['data'])
        logger.debug('end get ips.')

        return ips
    
    else:
        raise resp['message']


def scan():
    logger.debug('start scanning...')

    default_user = settings.DEVICE['user']
    default_password = settings.DEVICE['password']
    port = settings.DEVICE['port']

    try:
        ips = get_ips()
    except:
        logger.exception('Exception occured when get ips from platform')
        return
    
    pool = ThreadPoolExecutor(200)
    get_info_task = [pool.submit(get_info, ip) for ip in ips]

    new_sn_list_v = []
    new_data_list_v = []
    new_sn_list_k = []
    new_data_list_k = []
    for task in as_completed(get_info_task):
        try:
            ctype, response = task.result()
            if response is not None:
                if ctype == 'v':
                    if response['miner_sn'] not in new_sn_list_v:
                        new_sn_list_v.append(response['miner_sn'])
                        new_data_list_v.append(response)
                elif ctype == 'k':
                    if response['miner_sn'] not in new_sn_list_k:
                        new_sn_list_k.append(response['miner_sn'])
                        new_data_list_k.append(response)             
                else:
                    logger.debug(f"{response['miner_sn']} is registered")
        except:
            pass
    
    try:
        handle_device(new_sn_list_v, new_data_list_v, new_sn_list_k, new_data_list_k)
    except:
        logger.exception('handle error')
    
    logger.debug('end scannering.')


if __name__ == '__main__':
    scan()