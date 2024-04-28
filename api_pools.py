import time
import hmac,hashlib
import logging
from logInit import TimezoneRotatingFileHandler

from tenacity import retry, stop_after_attempt
import requests

import settings


logger = logging.getLogger('apipools')
logger.setLevel(settings.LOG['level'])
filename = settings.LOG['path'] + "apipools.log"
max_bytes = settings.LOG['max_bytes']
backup_count = settings.LOG['backup_count']
fh = TimezoneRotatingFileHandler(filename=filename, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s') 
fh.setFormatter(formatter)
logger.addHandler(fh)


@retry(
    reraise=True,
    stop=stop_after_attempt(2)
)
def get_2miners_data(coin_type:str):
    logger.debug('start get workers from 2miners...')

    pool_url = f'https://etc.2miners.com/api/accounts/0x8a417030c7Ecf1215d244Bf1Ae08EfAe7EeE23Fd'
    j = requests.get(pool_url, timeout=3).json()

    logger.debug(f'pool response from 2miners(etc): {j}')

    v = {}
    data_json = j['workers']
    for key in data_json.keys():
        worker = key.split(':')[0]
        m = {}
        m['hr_pool'] = data_json[key]['hr']
        m['hr_pool_1h'] = data_json[key]['hr']               # 处理为G为单位的数据
        m['hr_pool_24h'] = data_json[key]['hr2']
        m['reject_rate_pool'] = None
        v[worker.upper()] = m
    
    logger.debug('end get workers from 2miners:%s, %s', coin_type, v)

    return v


@retry(
    reraise=True,
    stop=stop_after_attempt(2)
)
def get_k1pool_data(coin_type:str):
    logger.debug('start get workers from k1pool...')

    account_ids = [
        "KrceSHAW7zARxQMjYrSRGnNSpH3Aw7jHQay"
    ]

    result = {}

    for account_id in account_ids:
        pool_url = f"https://k1pool.com/api/miner/{coin_type}/{account_id}"

        if settings.ENABLEPROXY == 1:
            proxies = {'http': settings.PROXYURL, 'https': settings.PROXYURL}
            r = requests.get(pool_url, proxies=proxies, timeout=3)
        else:
            r = requests.get(pool_url, timeout=3)
        
        j = r.json()
        logger.debug(f"{coin_type} workers response from ezil({account_id}): {j}")

        dd = {}
        data_dict:dict = j['miner']['workers']
        for k, v in data_dict.items():
            m = {}
            m['hr_pool'] = v['hr']
            m['hr_pool_1h'] = v['hr2']
            m['hr_pool_24h'] = v['hr24']
            m['reject_rate_pool'] = None
            dd[k.upper()] = m

        result.update(dd)
    
    logger.debug(f'end get workers from k1pool. return value({coin_type}) is {result}')

    return result


@retry(
    reraise=True,
    stop=stop_after_attempt(2)
)
def get_f2pool_data(coin_type: str):
    logger.debug(f'start get data from f2pool({coin_type})...')

    url = 'https://api.f2pool.com'
    user = 'ipollomini'

    if coin_type == 'etc':
        param = ''
    elif coin_type == 'eth':
        param = 'ethereum'
    elif coin_type == 'etf':
        param = 'ethereumfair'
    elif coin_type == 'ethw':
        param = 'ethereumpow'
    elif coin_type == 'zilliqa-etc':
        param = 'zilliqa-etc'
    else:
        logger.debug(f'f2pool({coin_type}) not allowed')
        return None
    
    pool_url = f'{url}/{param}/{user}'

    resp = requests.get(pool_url, timeout=3).json()
    logger.debug(f'works response from f2pool({coin_type}): {resp}')

    v = {}
    data_list = resp['workers']
    for data in data_list:
        miner = {}
        miner['hr_pool'] = data[1]
        miner['hr_pool_1h'] = data[2]
        miner['hr_pool_24h'] = int(data[4])/(60*60*24)
        if data[4] != 0:
            miner['reject_rate_pool'] = data[5]/data[4]
        else:
            miner['reject_rate_pool'] = None
        
        v[data[0].upper()] = miner
    
    logger.debug(f'end get data from f2pool({coin_type}): {v}.')

    return v


@retry(
    reraise=True,
    stop=stop_after_attempt(2)
)
def get_antpool_data(coin_type: str):

    def get_origin_value(data: str):
        data_list = data.split(" ")
        data_num = data_list[0]
        data_unit = data_list[1][0].upper()
        value = float(data_num) * settings.AVUNIT.setdefault(data_unit, 1)

        return value

    logger.debug(f'start get data from antpool({coin_type})...')

    sign_id = 'ipollomini'
    sign_key = '50e2dab3119c4bcab09c67d0ba70c65d'
    sign_SECRET = '1deb00ed435a4adf9a449d06505e0774'
    pool_url ='https://antpool.com/api/userWorkerList.htm'

    nonce = int(time.time()*1000)
    msgs = sign_id + sign_key + str(nonce)
    sign = hmac.new(key=sign_SECRET.encode(encoding='utf-8'),
                    msg=msgs.encode(encoding='utf-8'),
                    digestmod=hashlib.sha256).hexdigest().upper()
    
    parameter = {'key': sign_key, 'nonce': nonce, 'signature': sign, 'coin': coin_type.upper(), 'pageSize': 2000}

    resp = requests.post(url=pool_url, data=parameter, timeout=3).json()
    logger.debug(f'workers response from antpool({coin_type}): {resp}')

    code = resp['code']
    message = resp['message']

    if code != 0:
        return
    
    v = {}
    data_list = resp['data']['result']['rows']
    for data in data_list:
        miner = {}
        miner['hr_pool'] = get_origin_value(data['hsLast1h'])
        miner['hr_pool_1h'] = get_origin_value(data['hsLast1h'])
        miner['hr_pool_24h'] = get_origin_value(data['hsLast1d'])
        miner['reject_rate_pool'] = data['rejectRatio'][0:-1]

        v[data['workerId'].upper()] = miner
    
    logger.debug(f'end get workers from antpool({coin_type}): {v}.')

    return v


@retry(
    reraise=True,
    stop=stop_after_attempt(2)
)
def get_ezil_data(coin_type: str):
    logger.debug(f'start get data from ezil({coin_type})...')

    wallets = [
        '0x8831be6E603cE894546A78BE228B3BbE5563B16F.zil1khvxwpplyhx6a3sam6aytknrlxjc4wpm5h5kgt'
    ]

    v = {}
    for wallet in wallets:
        pool_url = f'https://stats.ezil.me/current_stats/{wallet}/workers/'
        resp = requests.get(url=pool_url, timeout=3).json()

        logger.debug(f'workers response from ezil({coin_type}): {resp}')

        wallet_value = {}
        data_list = resp
        for data in data_list:
            miner = {}
            miner['hr_pool'] = data['current_hashrate']     # 30min
            miner['hr_pool_1h'] = data['average_hashrate']      # 3h
            miner['hr_pool_24h'] = data['daily_hashrate']       # 24h
            miner['reject_rate_pool'] = None

            wallet_value[data['worker'].upper()] = miner
        
        v.update(wallet_value)
    
    logger.debug(f'end get workers from ezil({coin_type}): {v}.')

    return v


mapping = {
    'f2pool': get_f2pool_data,
    '8.212.2.228': get_f2pool_data,
    'antpool': get_antpool_data,
    'ezil': get_ezil_data,
    'k1pool': get_k1pool_data,
    '2miners': get_2miners_data
}


def get_pool_data():
    r = {}
    for pool, coin_types in settings.CURRENTPOOL.items():
        func = mapping[pool]

        r[pool] = {}
        for coin_type in coin_types:
            try:
                r[pool][coin_type] = func(coin_type)
            except:
                r[pool][coin_type] = None
                logger.exception(f'Exception occured when get pool data: {pool}({coin_type})')
    
    return r
