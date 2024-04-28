from logInit import TimezoneRotatingFileHandler
import logging

from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from typing import List, Union

import settings
from upgrade_task import get_device_ips
import api_pools, api_psu, api_miner
from k.vo import ApiData as ApiData_x
from v.vo import ApiData as ApiData_v
import data_handler

logger = logging.getLogger('minertask')
logger.setLevel(settings.LOG['level'])
filename = settings.LOG['path'] + "minertask.log"
max_bytes = settings.LOG['max_bytes']
backup_count = settings.LOG['backup_count']
fh = TimezoneRotatingFileHandler(filename=filename, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s') 
fh.setFormatter(formatter)
logger.addHandler(fh)


def handle_miner(new_sn_list_v, new_data_list_v, new_sn_list_k, new_data_list_k):
    logger.debug('start handle miner...')

    api_url_v = f"{settings.PLATFORM['url']+settings.PLATFORM['handle_miner_v']}"
    resp_v = requests.post(api_url_v, json={"sn": new_sn_list_v, "data": new_data_list_v}, timeout=100).json()

    api_url_k = f"{settings.PLATFORM['url']+settings.PLATFORM['handle_miner_k']}"
    resp_k = requests.post(api_url_k, json={"sn": new_sn_list_k, "data": new_data_list_k}, timeout=100).json()

    if resp_v['code'] == 0 and resp_k['code'] == 0:
        logger.debug('end handle miner.')
    
    else:
        raise resp_v['message'] + resp_k['message']


def scan():
    logger.debug('start scannering...')

    port = settings.DEVICE['api_port']

    try:
        ips = get_device_ips()
    except:
        logger.exception('Exception occured when get ips')
        return
    
    try:
        pool_data = api_pools.get_pool_data()
        # pool_data = []
    except:
        logger.exception('Exception occured when get pool workers')
    
    try:
        # temperature = api_psu.get_temperature()
        temperature = []
    except:
        logger.exception('Exception occured when get temperature')
        temperature = None
    
    try:
        power = api_psu.get_power()
    except:
        logger.exception('Exception occured when get power')
        power = None
    
    pool = ThreadPoolExecutor(200)
    get_info_task = [pool.submit(api_miner.get_info, ip, port) for ip in ips]

    new_sn_list_v = []
    new_data_list_v = []
    new_sn_list_k = []
    new_data_list_k = []
    for task in as_completed(get_info_task):
        try:
            ctype, api_data_list = task.result()
            if ctype == 'v':
                for api_data in api_data_list:
                    if api_data.miner_sn not in new_sn_list_v:
                        new_sn_list_v.append(api_data.miner_sn)
                        new_data_list_v.append(data_handler.handle_api_data(api_data, pool_data, temperature, power))
            elif ctype == 'k':
                for api_data in api_data_list:
                    if api_data.miner_sn not in new_sn_list_k:
                        new_sn_list_k.append(api_data.miner_sn)
                        new_data_list_k.append(data_handler.handle_api_data(api_data, pool_data, temperature, power))
        except:
            logger.exception('asc')
    
    try:
        handle_miner(new_sn_list_v, new_data_list_v, new_sn_list_k, new_data_list_k)
    except:
        logger.exception('handle error')
    
    logger.debug('scanning completed.')
    

if __name__ == '__main__':
    scan()
