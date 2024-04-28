from logInit import TimezoneRotatingFileHandler
import socket
import logging
import json
from typing import List, Dict
import requests

from tenacity import retry, stop_after_attempt, wait_random

from v.vo import ApiData
import settings


logger = logging.getLogger('apimine_v')
logger.setLevel(settings.LOG['level'])
filename = settings.LOG['path'] + "apiminer_v.log"
max_bytes = settings.LOG['max_bytes']
backup_count = settings.LOG['backup_count']
fh = TimezoneRotatingFileHandler(filename=filename, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s') 
fh.setFormatter(formatter)
logger.addHandler(fh)


@retry(
    reraise=True,
    wait=wait_random(min=6, max=12),
    stop=stop_after_attempt(2)
)
def call_api(ip, port, cmd_text):
    socket.setdefaulttimeout(5)    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, port))
        cmd_json = json.dumps(cmd_text).encode('utf-8')
        s.sendall(cmd_json)

        response = bytes()
        while True:
            buffer = s.recv(4096)
            if buffer:
                response = response + buffer
            else:
                break
    finally:
        s.close()

    a = response.replace(b'\x00', b'')
    b = a.replace(b'\n', b'')
    try:
        c = json.loads(b)
    except Exception as e:
        #logger.exception('%s %s parse json error: %s', ip, b, e)
        logger.exception('%s parse json error: %s', ip, b)
        c = None
    else:
        if type(c) is not dict:
            c = None
    return c


def build_info(api_data: ApiData, resp_info):
    api_data.miner_sn = resp_info['ASC'][0]['SN']
    api_data.model = resp_info['ASC'][0]['Model']
    api_data.hw_type = resp_info['ASC'][0]['HwType']
    api_data.sw_type = resp_info['ASC'][0]['SwType']
    api_data.version =resp_info['ASC'][0]['Version']
    api_data.os_version = resp_info['ASC'][0]['OsVer']
    api_data.firmware_version = 'notimp'
    api_data.bit_link = resp_info['ASC'][0]['FPGA Version']
    api_data.mac =  resp_info['ASC'][0]['MAC']
    api_data.api_ip =resp_info['ASC'][0]['IP']
    api_data.gateway = resp_info['ASC'][0]['Gateway']
    api_data.mask = resp_info['ASC'][0]['Netmask']
    api_data.vx = resp_info['ASC'][0]['VX']
    api_data.psu_model = resp_info['ASC'][0].setdefault('PSUModel', None)
    api_data.psu_serial = resp_info['ASC'][0].setdefault('PSUSerial', None)


def build_summary(api_data: ApiData, resp_summary):

    av_str = resp_summary['summary'][0]['SUMMARY'][0]['MHS av']
    _1m_str = resp_summary['summary'][0]['SUMMARY'][0]['MHS 1m']
    _5m_str = resp_summary['summary'][0]['SUMMARY'][0]['MHS 5m']
    _15m_str = resp_summary['summary'][0]['SUMMARY'][0]['MHS 15m']

    av_unit = av_str[-1].upper()
    av_num = av_str[0:-1]
    av_float = float(av_num) * settings.HRUNIT.setdefault(av_unit, 1)
    api_data.hr_local_g = av_float
    
    _1m_unit = _1m_str[-1].upper()
    _1m_num = _1m_str[0:-1]
    _1m_float = float(_1m_num) * settings.HRUNIT.setdefault(_1m_unit, 1)
    api_data.hr_local_1m_g = _1m_float
    
    _5m_unit = _5m_str[-1].upper()
    _5m_num = _5m_str[0:-1]
    _5m_float = float(_5m_num) * settings.HRUNIT.setdefault(_5m_unit, 1)
    api_data.hr_local_5m_g = _5m_float
    
    _15m_unit = _15m_str[-1].upper()
    _15m_num = _15m_str[0:-1]
    _15m_float = float(_15m_num) * settings.HRUNIT.setdefault(_15m_unit, 1)
    api_data.hr_local_15m_g = _15m_float

    api_data.hr_unit = settings.SHOWUNIT
    factor = settings.AVUNIT.setdefault(api_data.hr_unit)
    api_data.hr_local = (api_data.hr_local_g * 1000 * 1000 * 1000)/factor
    api_data.hr_local_1m = (api_data.hr_local_1m_g * 1000 * 1000 * 1000)/factor
    api_data.hr_local_5m = (api_data.hr_local_5m_g * 1000 * 1000 * 1000)/factor
    api_data.hr_local_15m = (api_data.hr_local_15m_g * 1000 * 1000 * 1000)/factor
    
    api_data.when = resp_summary['summary'][0]['STATUS'][0]['When']
    api_data.elapsed = resp_summary['summary'][0]['SUMMARY'][0]['Elapsed']

    accepted = resp_summary['summary'][0]['SUMMARY'][0]['Difficulty Accepted']
    api_data.accepted_local = accepted / (settings.AVUNIT.setdefault(settings.SHOWUNIT, 1))
    api_data.accepted_local_g = accepted / (1000*1000*1000)

    api_data.reject_rate_local = float(resp_summary['summary'][0]['SUMMARY'][0]['Pool Rejected%'])

    api_data.pool_url = 'no'
    api_data.pool_user = 'no'

    api_data.pool1_url = 'no'
    api_data.pool1_user = 'no'

    api_data.pool2_url = 'no'
    api_data.pool2_user = 'no'

    api_data.pool3_url = 'no'
    api_data.pool3_user = 'no'

    current_pool = resp_summary['devs'][0]['DEVS'][0]['Last Share Pool']

    pools = resp_summary['pools'][0]['POOLS']
    if pools is not None and len(pools) != 0:
        for x in pools:
            if x['POOL'] == current_pool:
                api_data.pool_url = x['URL']
                api_data.pool_user = x['User']

            if x['POOL'] == 0:
                api_data.pool1_url = x['URL']
                api_data.pool1_user = x['User']

            if x['POOL'] == 1:
                api_data.pool2_url = x['URL']
                api_data.pool2_user = x['User']

            if x['POOL'] == 2:
                api_data.pool3_url = x['URL']
                api_data.pool3_user = x['User']


def build_status(api_data: ApiData, resp_status):
    api_data.vout = resp_status['ASC'][0]['Vout']
    api_data.iout = resp_status['ASC'][0]['Iout']
    api_data.pout = resp_status['ASC'][0]['Pout']
    
    api_data.psu_ver = resp_status['ASC'][0]['PsuVer']
    api_data.psu_err = resp_status['ASC'][0]['PsuErr']
    api_data.g_status = resp_status['ASC'][0]['GStatus']
    api_data.r_status = resp_status['ASC'][0]['RStatus']
    api_data.r_interval = resp_status['ASC'][0]['RInterval']
    api_data.g_interval = resp_status['ASC'][0]['GInterval']
    api_data.fan_speed = [
        resp_status['ASC'][0]['roundSpeed0'],
        resp_status['ASC'][0]['roundSpeed1'],
        resp_status['ASC'][0]['roundSpeed2'],
        resp_status['ASC'][0]['roundSpeed3']
    ]
    api_data.c_temp = resp_status['ASC'][0]['CTemp']

    api_data.uptm = resp_status['ASC'][0]['uptm']


def build_chips(api_data: ApiData, resp_chips):
    r = {}
    temp = resp_chips['ASC'][0]['temp']
    temp_list = temp.split(",")
    r['temp'] = [float(x) for x in temp_list]

    freq = resp_chips['ASC'][0]['freq']
    freq_list = freq.split(",")
    r['freq'] = [float(x) for x in freq_list if x!='']

    vol = resp_chips['ASC'][0]['vol']
    vol_list = vol.split(",")
    r['vol'] = [float(x) for x in vol_list if x!='']

    r['cpid'] = resp_chips['ASC'][0]['cpid']
    r['curr'] = resp_chips['ASC'][0]['curr']

    try:
        r['hwver'] = resp_chips['ASC'][0]['hwver']
    except Exception as e:
        logger.exception('%s: chips hwver error', api_data.scan_ip)

    api_data.chips = r


def build_datas(api_data: ApiData, resp_datas):
    r = {}

    datas = resp_datas['ASC'][0]['datas']
    datas_list = datas.split(',')
    r['datas'] = [int(x) for x in datas_list]

    rject = resp_datas['ASC'][0]['rject']
    rject_list = rject.split(',')
    r['rject'] = [int(x) for x in rject_list]

    try:
        hwerr = resp_datas['ASC'][0]['hwerr']
        hwerr_list = hwerr.split(',')
        r['hwerr'] = [int(x) for x in hwerr_list]

        stale = resp_datas['ASC'][0]['stale']
        stale_list = stale.split(',')
        r['stale'] = [int(x) for x in stale_list]

        dupli = resp_datas['ASC'][0]['dupli']
        dupli_list = dupli.split(',')
        r['dupli'] = [int(x) for x in dupli_list]

        diff = resp_datas['ASC'][0]['diff']
        diff_list = diff.split(',')
        r['diff'] = [int(x) for x in diff_list]

        power = resp_datas['ASC'][0]['power']
        power_list = power.split(',')
        r['power'] = [float(x) for x in power_list]

        smerr = resp_datas['ASC'][0]['smerr']
        smerr_list = smerr.split(',')
        r['smerr'] = [int(x) for x in smerr_list]

        nonce1 = resp_datas['ASC'][0]['nonce1']
        nonce1_list = nonce1.split(',')
        r['nonce1'] = [int(x) for x in nonce1_list]

        reject1 = resp_datas['ASC'][0]['reject1']
        reject1_list = reject1.split(',')
        r['reject1'] = [int(x) for x in reject1_list]

        hwer1 = resp_datas['ASC'][0]['hwer1']
        hwer1_list = hwer1.split(',')
        r['hwer1'] = [int(x) for x in hwer1_list]

        no1ratio = resp_datas['ASC'][0]['no1ratio']
        no1ratio_list = no1ratio.split(',')
        r['no1ratio'] = [int(x) for x in no1ratio_list]

        rstcnt = resp_datas['ASC'][0]['rstcnt']
        rstcnt_list = rstcnt.split(',')
        r['rstcnt'] = [int(x) for x in rstcnt_list]

    except Exception as e:
        logger.exception('%s: hwerr stale dupli error', api_data.scan_ip)

    try:
        closed = resp_datas['ASC'][0]['closed']
        r['closed'] = closed

        all_closed = []
        for k, v in closed.items():
            all_closed.extend(v)
        r['all_closed'] = all_closed
    except Exception as e:
        logger.exception('%s: closed core does not exist', api_data.scan_ip)

    api_data.datas = r


def build_hbsn(api_data: ApiData, resp_hbsn):
    r= {}
    hbsn = resp_hbsn['ASC'][0]['HBSN']
    r['chain0'] = hbsn['chain0']
    r['chain1'] = hbsn['chain1']
    r['chain2'] = hbsn['chain2']

    api_data.hbsn = r


def build_cores(api_data: ApiData, resp_cores0, resp_cores1, resp_cores2):
    r = {}

    accept0 = resp_cores0['ASC'][0]['chain0accept']
    accept0_list = accept0.split(',')
    r['chain0accept'] = [int(x) for x in accept0_list]

    reject0 = resp_cores0['ASC'][0]['chain0reject']
    reject0_list = reject0.split(',')
    r['chain0reject'] = [int(x) for x in reject0_list]

    hwer0 = resp_cores0['ASC'][0]['chain0hwer']
    hwer0_list = hwer0.split(',')
    r['chain0hwer'] = [int(x) for x in hwer0_list]

    accept1 = resp_cores1['ASC'][0]['chain1accept']
    accept1_list = accept1.split(',')
    r['chain1accept'] = [int(x) for x in accept1_list]

    reject1 = resp_cores1['ASC'][0]['chain1reject']
    reject1_list = reject1.split(',')
    r['chain1reject'] = [int(x) for x in reject1_list]

    hwer1 = resp_cores1['ASC'][0]['chain1hwer']
    hwer1_list = hwer1.split(',')
    r['chain1hwer'] = [int(x) for x in hwer1_list]

    accept2 = resp_cores2['ASC'][0]['chain2accept']
    accept2_list = accept2.split(',')
    r['chain2accept'] = [int(x) for x in accept2_list]

    reject2 = resp_cores2['ASC'][0]['chain2reject']
    reject2_list = reject2.split(',')
    r['chain2reject'] = [int(x) for x in reject2_list]

    hwer2 = resp_cores2['ASC'][0]['chain2hwer']
    hwer2_list = hwer2.split(',')
    r['chain2hwer'] = [int(x) for x in hwer2_list]

    api_data.cores = r


def build_memo(api_data: ApiData, resp_memo):
    if api_data.extra_cmds is None:
        api_data.extra_cmds = {}
    
    api_data.extra_cmds['memo'] = resp_memo['ASC'][0]


def build_mempll(api_data: ApiData, resp_mempll):
    if api_data.extra_cmds is None:
        api_data.extra_cmds = {}
    
    api_data.extra_cmds['mempll'] = resp_mempll['ASC'][0]


def build_hmode(api_data: ApiData, resp_hmode):
    if api_data.extra_cmds is None:
        api_data.extra_cmds = {}
    
    api_data.extra_cmds['hmode'] = resp_hmode['ASC'][0]


def build_boost(api_data: ApiData, resp_boost):
    if api_data.extra_cmds is None:
        api_data.extra_cmds = {}
    
    api_data.extra_cmds['boost'] = resp_boost['ASC'][0]['get getv7boost']


def check_api_data(api_data: ApiData, error_msg: dict):
    return None


def get_api(ip, port):
    cmds = {
        "info": {"command": "ascset", "parameter": "0,info,null"},
        "summary": {"command": "summary+pools+devs"},
        "status": {"command": "ascset", "parameter": "0,status,null"},
        "chips": {"command": "ascset", "parameter": "0,chips,null"},
        "datas": {"command": "ascset", "parameter": "0,datas,null"},
        "hbsn": {"command": "ascset", "parameter": "0,hbsn,null"},
        "cores0": {"command": "ascset", "parameter": "0,cores,0x00"},
        "cores1": {"command": "ascset", "parameter": "0,cores,0x01"},
        "cores2": {"command": "ascset", "parameter": "0,cores,0x02"},
        "memo": {"command": "ascset", "parameter": "0,memo,0x00"},
        "mempll": {"command": "ascset", "parameter": "0,readreg,mempll"},
        "agingmode": {"command": "ascset", "parameter": "0,writereg,agingmode"},
        "hmode": {"command":"ascset", "parameter":"0,getmode,null"},
        "boost": {"command": "ascset", "parameter": "0,writereg,getv7boost"}
    }

    api_data = ApiData()
    api_data.scan_ip = ip

    error_msg = {}

    resp_aging = None
    try:
        resp_aging = call_api(ip, port, cmds['agingmode'])
        logger.debug(f'{ip} agingmode result: {resp_aging}')
    except:
        logger.exception(f'{ip} exception occured when call agingmode')

    resp_hmode = None
    try:
        resp_hmode = call_api(ip, port, cmds['hmode'])
        logger.debug(f'{ip} hmode result: {resp_hmode}')

        build_hmode(api_data, resp_hmode)
    except:
        logger.exception(f'{ip} exception occured when call hmode')
    
    resp_boost = None
    try:
        resp_boost = call_api(ip, port, cmds['boost'])
        logger.debug(f'{ip} boost result: {resp_boost}')

        build_boost(api_data, resp_boost)
    except:
        logger.exception(f'{ip} exception occured when call boost')
    
    resp_info = None
    try:
        resp_info = call_api(ip, port, cmds['info'])
        logger.debug(f'{ip} info result: {resp_info}')

        build_info(api_data, resp_info)
    except:
        logger.debug(f'{ip} exception occured when call info')
        raise
    
    resp_summary = None
    try:
        resp_summary = call_api(ip, port, cmds['summary'])
        logger.debug(f'{ip} summary result: {resp_summary}')

        build_summary(api_data, resp_summary)
    except:
        logger.exception(f'{ip} exception occured when call summary')
        raise

    resp_status = None
    try:
        resp_status = call_api(ip, port, cmds['status'])
        logger.debug(f'{ip} status result: {resp_status}')

        build_status(api_data, resp_status)
    except:
        logger.exception(f'{ip} exception occured when call status')
        raise
    
    resp_chips = None
    try:
        resp_chips = call_api(ip, port, cmds['chips'])
        logger.debug(f'{ip} chips result: {resp_chips}')

        build_chips(api_data, resp_chips)
    except:
        logger.exception(f'{ip} exception occured when call chips')
    
    resp_datas = None
    try:
        resp_datas = call_api(ip, port, cmds['datas'])
        logger.debug(f'{ip} datas result: {resp_datas}')

        build_datas(api_data, resp_datas)
    except:
        logger.exception(f'{ip} exception occured when call datas')
    
    resp_hbsn = None
    try:
        resp_hbsn = call_api(ip, port, cmds['hbsn'])
        logger.debug(f'{ip} hbsn result: {resp_hbsn}')

        build_hbsn(api_data, resp_hbsn)
    except:
        logger.exception(f'{ip} exception occured when call hbsn')
    
    resp_cores0 = None
    try:
        resp_cores0 = call_api(ip, port, cmds['cores0'])
        logger.debug(f'{ip} cores0 result: {resp_cores0}')
    except:
        logger.exception(f'{ip} exception occured when call cores0')
    
    resp_cores1 = None
    try:
        resp_cores1 = call_api(ip, port, cmds['cores1'])
        logger.debug(f'{ip} cores1 result: {resp_cores1}')
    except:
        logger.exception(f'{ip} exception occured when call cores1')
    
    resp_cores2 = None
    try:
        resp_cores2 = call_api(ip, port, cmds['cores2'])
        logger.debug(f'{ip} cores2 result: {resp_cores2}')

        build_cores(api_data, resp_cores0, resp_cores1, resp_cores2)
    except:
        logger.exception(f'{ip} exception occured when call cores2')
    
    resp_memo = None
    try:
        resp_memo = call_api(ip, port, cmds['memo'])
        logger.debug(f'{ip} memo result: {resp_memo}')

        build_memo(api_data, resp_memo)
    except:
        logger.exception(f'{ip} exception occured when call memo')   
    
    resp_mempll = None
    try:
        resp_mempll = call_api(ip, port, cmds['mempll'])
        logger.debug(f'{ip} mempll result: {resp_mempll}')

        build_mempll(api_data, resp_mempll)
    except:
        logger.exception(f'{ip} exception occured when call mempll')

    check_api_data(api_data, error_msg)

    api_data.error_msg = error_msg

    logger.debug(f'scanning {ip}:{port} completed.')

    return [api_data]
