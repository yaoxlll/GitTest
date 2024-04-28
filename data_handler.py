import logging
from logInit import TimezoneRotatingFileHandler
from dataclasses import asdict

from typing import Union

from k.vo import ApiData as ApiData_k
from v.vo import ApiData as ApiData_v
import settings


logger = logging.getLogger('datahandler')
logger.setLevel(settings.LOG['level'])
filename = settings.LOG['path'] + "datahandler.log"
max_bytes = settings.LOG['max_bytes']
backup_count = settings.LOG['backup_count']
fh = TimezoneRotatingFileHandler(filename=filename, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s') 
fh.setFormatter(formatter)
logger.addHandler(fh)


def set_pool_data(api_data: Union[ApiData_k, ApiData_v], pool_data: dict):
    logger.debug(f'{api_data.scan_ip} start set pool data...')

    if pool_data is not None:
        worker_list = api_data.pool_user.split(".")
        if len(worker_list) == 1:
            worker = worker_list[0]
        else:
            worker = worker_list[-1]
        
        data = pool_data.setdefault(worker.upper(), None)
        logger.debug(f'pool worker({worker.upper()}): {data}')

        if data is not None:
            factor = settings.AVUNIT.setdefault(api_data.hr_unit, 1)

            if data['hr_pool'] is not None:
                api_data.hr_pool = float(data['hr_pool'])/factor
            
            if data['hr_pool_1h'] is not None:
                api_data.hr_pool_1h = float(data['hr_pool_1h'])/factor

            if data['hr_pool_24h'] is not None:
                api_data.hr_pool_24h = float(data['hr_pool_24h'])/factor

            if data['reject_rate_pool'] is not None:
                api_data.reject_rate_pool = float(data['reject_rate_pool'])
    
    logger.debug(f'{api_data.scan_ip} end set pool data.')


def handle_api_data(api_data: Union[ApiData_k, ApiData_v], pool_data: dict, temperature: dict, power: dict):
    logger.debug(f'{api_data.scan_ip} start handle bench data...')

    try:
        api_data.hr_unit = settings.SHOWUNIT
        api_data.power_consume = api_data.pout / 0.94 + 70

        api_data.coin_type = 'unknown'

        for key, value in settings.POOLS.items():
            if key in api_data.pool_url:
                api_data.coin_type = value
                break
                
        if temperature is not None:
            api_data.env_temp = temperature['temp']
            api_data.env_humi = temperature['humi']
        
        if power is not None:
            iip = api_data.scan_ip
            if iip in power.keys():
                api_data.instru_v = float(power[iip]['v'])
                api_data.instru_i = float(power[iip]['i'])
                api_data.instru_ap = float(power[iip]['ap'])*1000
        
        for key, value in settings.CURRENTPOOL.items():
            if key in api_data.pool_url:
                if api_data.coin_type in value:
                    set_pool_data(api_data, pool_data[key][api_data.coin_type])
    
    except:
        logger.exception(f'{api_data.scan_ip} exception occured when handle bench data')
    
    logger.debug(f'{api_data.scan_ip} end handle bench data.')

    return asdict(api_data)
