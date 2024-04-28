from logInit import TimezoneRotatingFileHandler
import socket
import logging
import json
from typing import List, Dict
import requests

from tenacity import retry, stop_after_attempt, wait_random

from k.vo import ApiData
import settings


logger = logging.getLogger('apimine_x')
logger.setLevel(settings.LOG['level'])
filename = settings.LOG['path'] + "apiminer_x.log"
max_bytes = settings.LOG['max_bytes']
backup_count = settings.LOG['backup_count']
fh = TimezoneRotatingFileHandler(filename=filename, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s') 
fh.setFormatter(formatter)
logger.addHandler(fh)


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

    resp_info = None
    try:
        resp_info = call_api(ip, port, cmds['info'])
        logger.debug(f'{ip} info result: {resp_info}')
    except:
        logger.exception(f'{ip} exception occured when call info')
        raise

    resp_summary = None
    try:
        resp_summary = call_api(ip, port, cmds['summary'])
        logger.debug(f'{ip} summary result: {resp_summary}')
    except:
        logger.exception(f'{ip} exception occured when call summary')
        raise

    resp_status = None
    try:
        resp_status = call_api(ip, port, cmds['status'])
        logger.debug(f'{ip} status result: {resp_status}')
    except:
        logger.exception(f'{ip} exception occured when call status')
        raise

    resp_chips = {'ASC': [None]}
    try:
        resp_chips = call_api(ip, port, cmds['chips'])
        logger.debug(f'{ip} chips result: {resp_chips}')
    except:
        logger.exception(f'{ip} exception occured when call chips')
        raise

    resp_datas = {'ASC': None}
    try:
        resp_datas = call_api(ip, port, cmds['datas'])
        logger.debug(f'{ip} datas result: {resp_datas}')
    except:
        logger.exception(f'{ip} exception occured when call datas')
        raise

    resp_hbsn = {'ASC': None}
    try:
        resp_hbsn = call_api(ip, port, cmds['hbsn'])
        logger.debug(f'{ip} hbsn result: {resp_hbsn}')
    except:
        logger.exception(f'{ip} exception occured when call hbsn')
        raise

    resp_memo = {'ASC': None}
    try:
        resp_memo = call_api(ip, port, cmds['memo'])
        logger.debug(f'{ip} memo result: {resp_memo}')
    except:
        logger.exception(f'{ip} exception occured when call memo')
        raise

    resp_mempll = {'ASC': [None]}
    try:
        resp_mempll = call_api(ip, port, cmds["mempll"])
        logger.debug('%s mempll result: %s', ip, resp_mempll)
    except Exception as e:
        logger.exception(f'{ip} exception occured when call mempll')

    resp_aging = {'ASC': None}
    try:
        resp_aging = call_api(ip, port, cmds['agingmode'])
        logger.debug(f'{ip} agingmode result: {resp_aging}')
    except:
        logger.exception(f'{ip} exception occured when call agingmode')
        raise

    resp_hmode = {'ASC': None}
    try:
        resp_hmode = call_api(ip, port, cmds['hmode'])
        logger.debug(f'{ip} hmode result: {resp_hmode}')
    except:
        logger.exception(f'{ip} exception occured when call hmode')
        raise
    
    resp_boost = {'ASC': None}
    try:
        resp_boost = call_api(ip, port, cmds['boost'])
        logger.debug(f'{ip} boost result: {resp_boost}')
    except:
        logger.exception(f'{ip} exception occured when call boost')
        raise

    try:
        api_data_list = build_api_data(
            ip=ip,
            info=resp_info['ASC'][0],
            summary=resp_summary,
            status=resp_status['ASC'][0],
            chips=resp_chips['ASC'][0],
            datas=resp_datas['ASC'][0],
            hbsn=resp_hbsn['ASC'][0],
            memo=resp_memo['ASC'][0],
            mempll=resp_mempll['ASC'][0],
            hmode=resp_hmode['ASC'][0],
            boost=resp_boost['ASC'][0]
        )
    except:
        logger.exception(f'{ip} exception occured when call build api data')
        raise

    logger.debug(f'scanning {ip}:{port} completed.')

    return api_data_list


def build_api_data(
        ip: str,
        info: dict,
        summary: dict,
        status: dict,
        chips: dict,
        datas: dict,
        hbsn: dict,
        memo: dict,
        mempll: dict,
        hmode: dict,
        boost: dict
) -> List[ApiData]:
    
    result = []

    status_fanspeed = status['card']['fanspeed']

    status_redled_list = status['card']['redled']
    sub_of_data = [i for i, element in enumerate(status_redled_list) if element != '-1']    # card online, [1,2,5]

    status_avg_list = status['card']['avg']

    if chips is not None:
        try:
            chips_temp: str = chips['temp']
            chips_temp_list: List[int] = [int(temp) for temp in chips_temp.split(',')]

            chips_freq: str = chips['freq']
            chips_freq_list: List[int] = [int(freq) for freq in chips_freq.split(',')]

            chips_vol: str = chips['vol']
            chips_vol_list: List[int] = [int(vol) for vol in chips_vol.split(',')]

            chips_cpid: str = chips['cpid']
            chips_cpid_list: List[str] = chips_cpid.split(',')

            chips_curr: str = chips['curr']
            chips_curr_list: List[int] = [int(curr) for curr in chips_curr.split(',')]

            chips_slots: str = chips['slots']
            chips_slots_list: List[str] = chips_slots.split(',')

            chips_hwver: str = chips['hwver']
            chips_hwver_list: List[str] = chips_hwver.split(',')
        except:
            logger.exception(f'{ip} exception occured when build api data(chips)')
    
    if datas is not None:
        try:
            datas_datas: str = datas['datas']
            datas_datas_list: List[int] = [int(x) for x in datas_datas.split(',')]

            datas_rject: str = datas['rject']
            datas_rject_list: List[int] = [int(x) for x in datas_rject.split(',')]

            datas_hwerr: str = datas['hwerr']
            datas_hwerr_list: List[int] = [int(x) for x in datas_hwerr.split(',')]

            datas_stale: str = datas['stale']
            datas_stale_list: List[int] = [int(x) for x in datas_stale.split(',')]

            datas_dupli: str = datas['dupli']
            datas_dupli_list: List[int] = [int(x) for x in datas_dupli.split(',')]

            datas_diff: str = datas['diff']
            datas_diff_list: List[str] = datas_diff.split(',')

            datas_power: str = datas['power']
            datas_power_list: List[float] = [float(x) for x in datas_power.split(',')]

            datas_smerr: str = datas['smerr']
            datas_smerr_list: List[int] = [int(x) for x in datas_smerr.split(',')]

            datas_nonce1: str = datas['nonce1']
            datas_nonce1_list: List[int] = [int(x) for x in datas_nonce1.split(',')]

            datas_reject1: str = datas['reject1']
            datas_reject1_list: List[int] = [int(x) for x in datas_reject1.split(',')]

            datas_hwer1: str = datas['hwer1']
            datas_hwer1_list: List[int] = [int(x) for x in datas_hwer1.split(',')]

            datas_no1ratio: str = datas['no1ratio']
            datas_no1ratio_list: List[int] = [int(x) for x in datas_no1ratio.split(',')]

            datas_closed: str = datas['closed']

            datas_avg: str = datas['avg']
            datas_avg_list: List[float] = [float(x) for x in datas_avg.split(',')]
        except:
            logger.exception(f'{ip} exception occured when build api datas(datas)')

    if hbsn is not None:
        try:
            hbsn_hbsn: dict = hbsn['HBSN']
            hbsn_hbsn_list = []
            for k, v in hbsn_hbsn.items():
                hbsn_hbsn_list.extend(v)
        except:
            logger.exception(f'{ip} exception occured when build api data(hbsn)')
        
    if memo is not None:
        try:
            memo_good: str = memo['good']
            memo_good_list: List[int] = [int(x) for x in memo_good.split(',')]

            memo_ndrp: str = memo['ndrp']
            memo_ndrp_list: List[int] = [int(x) for x in memo_ndrp.split(',')]

            memo_elmt: str = memo['elmt']
            memo_elmt_list: List[int] = [int(x) for x in memo_elmt.split(',')]

            memo_rpar: str = memo['rpar']
            memo_rpar_list: List[int] = [int(x) for x in memo_rpar.split(',')]

            memo_stmn: str = memo['stmn']
            memo_stmn_list: List[int] = [int(x) for x in memo_stmn.split(',')]

            memo_hwer: str = memo['hwer']
            memo_hwer_list: List[int] = [int(x) for x in memo_hwer.split(',')]

            memo_hrat: str = memo['hrat']
            memo_hrat_list: List[int] = [int(x) for x in memo_hrat.split(',')]

            memo_dupl: str = memo['dupl']
            memo_dupl_list: List[int] = [int(x) for x in memo_dupl.split(',')]

            memo_dcore: str = memo['dcore']
            #memo_dcore_list: List[int] = [int(x) for x in memo_dcore.split(',')]

            memo_prev2: int = memo['prev2']

            memo_prev3: int = memo['prev3']

            memo_cpidx: str = memo['cpidx']
            #memo_cpidx_list: List[int] = [int(x) for x in memo_cpidx.split(',')]

            memo_avgn: str = memo['avgn']
            #memo_avgn_list: List[int] = [int(x) for x in memo_avgn.split(',')]

            memo_ratio2: str = memo['ratio2']
            #memo_ratio2_list: List[int] = [int(x) for x in memo_ratio2.split(',')]
        except Exception as e:
            logger.exception(f'{ip} exception occured when build api data(memo)')
    
    if mempll is not None:
        try:
            mempll_mempll: str = mempll['mempll']
            mempll_mempll_list: List[int] = [int(mempll) for mempll in mempll_mempll.split(',')]
        except:
            logger.exception(f'{ip} exception occured when build api data(mempll)')
    
    if boost is not None:
        try:
            boost_boost: str = boost['get getv7boost']
            boost_boost_list: List[int] = [int(boost) for boost in boost_boost.split(',')]
        except:
            logger.exception(f'{ip} exception occured when build api data(boost)')
    
    for sub in sub_of_data:
        api_data = ApiData()
        api_data.name = f'{sub}'
        api_data.scan_ip = ip

        #info
        api_data.sn = info['SN']
        api_data.miner_sn = hbsn_hbsn_list[sub]
        api_data.model = info['Model']
        api_data.hw_type = info['HwType']
        api_data.sw_type = info['SwType']
        api_data.version =info['Version']
        api_data.os_version = info['OsVer']
        api_data.fpga_version = info['FPGA Version']
        api_data.cb = info['CB']
        api_data.mac =  info['MAC']
        api_data.api_ip =info['IP']
        api_data.gateway = info['Gateway']
        api_data.mask = info['Netmask']
        api_data.vx = info['VX']
        api_data.psu_model = info.get('PSUModel', None)
        api_data.psu_serial = info.get('PSUSerial', None)

        # summary
        build_summary(api_data, summary)

        # status
        api_data.vout = status['Vout']
        api_data.iout = status['Iout']
        api_data.pout = status['Pout']
        api_data.psu_ver = status['PsuVer']
        api_data.psu_err = status['PsuErr']
        api_data.g_status = status['GStatus']
        api_data.r_status = status['RStatus']
        api_data.g_interval = status['GInterval']
        api_data.r_interval = status['RInterval']
        api_data.round_speed = [
            status['roundSpeed0'],
            status['roundSpeed1'],
            status['roundSpeed2'],
            status['roundSpeed3']
        ]
        b: List[str] = status_fanspeed.get(f'card{sub}')
        api_data.fan_speed = b[0].split(',')
        api_data.red_led = status_redled_list[sub]
        api_data.c_temp = status['CTemp']
        api_data.uptm = status['uptm']
        api_data.hr_local = float(status_avg_list[sub])
    
        # chips
        if chips is not None:
            try:
                api_data.chips = {
                    'temp': chips_temp_list[sub],
                    'freq': chips_freq_list[sub],
                    'vol': chips_vol_list[sub],
                    'cpid': chips_cpid_list[sub],
                    'curr': chips_curr_list[sub],
                    'slots': chips_slots_list[sub],
                    'hwver': chips_hwver_list[sub],
                }
            except Exception as e:
                logger.exception(f'{ip}({sub}) exception occured in chips')
        
        # datas
        if datas is not None:
            try:
                api_data.datas = {
                    'datas': datas_datas_list[sub],
                    'rject': datas_rject_list[sub],
                    'hwerr': datas_hwerr_list[sub],
                    'stale': datas_stale_list[sub],
                    'dupli': datas_dupli_list[sub],
                    'diff': datas_diff_list[sub],
                    'power': datas_power_list[sub],
                    'smerr': datas_smerr_list[sub],
                    'nonce1': datas_nonce1_list[sub],
                    'reject1': datas_reject1_list[sub],
                    'hwer1': datas_hwer1_list[sub],
                    'no1ratio': datas_no1ratio_list[sub],
                    'closed': datas_closed.get(f'chipid{sub}'),
                    'avg': datas_avg_list[sub],
                }
            except Exception as e:
                logger.exception(f'{ip}({sub}) exception occured in datas')
        
        # cores
        try:
            cmd = {"command": "ascset", "parameter": f"0,cores,0x{'{:02x}'.format(sub)}"}
            logger.debug(f'{ip}({sub}) call cores with parameter: {cmd}')

            resp_cores = call_api(ip, settings.DEVICE['api_port'], cmd)
            logger.debug(f'{ip}({sub}) cores result: {resp_cores}')

            cores_cores = resp_cores['ASC'][0]
            cores_accept = cores_cores.get(f'chain{sub}accept')
            cores_reject = cores_cores.get(f'chain{sub}reject')
            cores_hwer = cores_cores.get(f'chain{sub}hwer')

            api_data.cores = {
                'accept': cores_accept,
                'reject': cores_reject,
                'hwer': cores_hwer
            }
        
        except:
            logger.exception(f'{ip}({sub}) exception occured when call cores')
        
        # memo
        if memo is not None:
            try:
                api_data.memo = {
                    'good': memo_good_list[sub],
                    'ndrp': memo_ndrp_list[sub],
                    'elmt': memo_elmt_list[sub],
                    'rpar': memo_rpar_list[sub],
                    'stmn': memo_stmn_list[sub],
                    'hwer': memo_hwer_list[sub],
                    'hrat': memo_hrat_list[sub],
                    'dupl': memo_dupl_list[sub],
                    'dcore': memo_dcore,
                    'prev2': memo_prev2,
                    'prev3': memo_prev3,
                    'cpidx': memo_cpidx,
                    'avgn': memo_avgn,
                    'ratio2': memo_ratio2,
                }
            except Exception as e:
                logger.exception(f'{ip}({sub}) exception occured when call memo')

        #mempll
        if mempll is not None:
            try:
                api_data.mempll = {
                    'mempll': mempll_mempll_list[sub],
                }
            except Exception as e:
                logger.exception(f'{ip}({sub}) exception occured when call mempll')

        #hmode
        if hmode is not None:
            try:
                api_data.mode = {
                    'hmode': hmode['hmode'],
                }
            except Exception as e:
                logger.exception(f'{ip}({sub}) exception occured when call hmode')

        #v7boost
        if boost is not None:
            try:
                api_data.boost = {
                    'boost': boost_boost_list[sub],
                }
            except Exception as e:
                logger.exception(f'{ip}({sub}) exception occured when call boost')
        
        result.append(api_data)
    
    return result


def build_summary(api_data: ApiData, resp_summary):
    av_str = resp_summary['summary'][0]['SUMMARY'][0]['MHS av']
    av_unit = av_str[-1].upper()
    av_num = av_str[0:-1]
    av_float_g = float(av_num) * settings.HRUNIT.setdefault(av_unit, 1)
    av_float_show_unit = float(av_float_g) / settings.HRUNIT.setdefault(settings.SHOWUNIT, 1)
    if api_data.extra_cmds is None:
        api_data.extra_cmds = {}
    
    api_data.extra_cmds['hrLocalTotal'] = av_float_show_unit
    
    api_data.when = resp_summary['summary'][0]['STATUS'][0]['When']
    api_data.elapsed = resp_summary['summary'][0]['SUMMARY'][0]['Elapsed']

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
