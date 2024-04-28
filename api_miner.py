# from logInit import TimezoneRotatingFileHandler
from logInit import TimezoneRotatingFileHandler
import socket
import logging
import json
from typing import List, Dict
import requests

from tenacity import retry, stop_after_attempt, wait_random

import settings

import k.handle_api as handle_api_x
import v.handle_api as handle_api_v


logger = logging.getLogger('apiminer')
logger.setLevel(settings.LOG['level'])
filename = settings.LOG['path'] + "apiminer.log"
max_bytes = settings.LOG['max_bytes']
backup_count = settings.LOG['backup_count']
fh = TimezoneRotatingFileHandler(filename=filename, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s') 
fh.setFormatter(formatter)
logger.addHandler(fh)


def get_hwinfo(ip):
    try:
        url = f"http://{ip}/cgi-bin/luci/admin/ipollo_main/ipollo_devinfo"
        r = requests.get(url, timeout=3).json()
        logger.debug('hwinfo for %s: %s', ip, r)
        return r
    except Exception as e:
        logger.exception('exception occured when get hwinfo for %s', ip)
        return {}


def get_info(ip, port):
    logger.debug(f'start scanning {ip}:({port})....')

    try:
        hwinfo_dict = get_hwinfo(ip)
        if len(hwinfo_dict.keys()) == 0:
            logger.debug(f'{ip} hwinfo is empty')
            raise

        hw_type = hwinfo_dict['HwType']
        miner_sn = hwinfo_dict['SN']

        miner_hw_type = settings.MINER_HWTYPE_V + settings.MINER_HWTYPE_K
        if len(miner_hw_type) != 0:
            if hw_type not in miner_hw_type:
                logger.debug(f'{ip}({hw_type}) not in config hwtype')
                raise
        
        if len(miner_sn) == 0:
            logger.debug(f'{ip}({miner_sn}) sn is blank')
            raise
    
    except:
        logger.exception(f'{ip} exception occured when getting hw_type')
        raise

    # DEVICE_HWTYPE_X
    if hw_type in settings.MINER_HWTYPE_K:
        api_data = handle_api_x.get_api(ip, port)

        return "k", api_data

    if hw_type in settings.MINER_HWTYPE_V:
        api_data = handle_api_v.get_api(ip, port)
    
        return "v", api_data
    

if __name__ == '__main__':
    ctype, resp = get_info("192.168.106.93", 4028)
    print(resp)
