DEVICE = {
    'user': 'root',
    'password': 'root',
    'port': 22,
    'api_port': 4028
}


LOG = {
    'path': '/opt/benchmis/logs/scanner/',
    'level': 'DEBUG',
    'max_bytes': 1024*1024*1000,
    'backup_count': 10
}

TIME_ZONE = 'Asia/Shanghai'


PLATFORM = {
    'url': 'http://127.0.0.1:8000',
    # 'url': 'http://192.168.122.1:30007',
    'get_ips': '/bench/api/ip/',
    'handle_device_v': '/miners/v/scanner/device/',
    'handle_device_k': '/miners/k/scanner/device/',
    'handle_miner_v': '/miners/v/scanner/bench/',
    'handle_miner_k': '/miners/k/scanner/bench/',
    'firmware_data': '/bench/api/firmware/',
    'bench_device_ip': '/bench/api/deviceip/'
}


DEVICE_HWTYPE_K = ['XHSE', 'XH1']
DEVICE_HWTYPE_V = ['C11', 'C11W', 'C1X', 'C1XW', 'CV1', 'CV1W']
DEVICE_MODEL_ESA = ['F1', 'W1']

MINER_HWTYPE_K = ['XHSE', 'XH1']
MINER_HWTYPE_V = ['C11', 'C11W', 'C1X', 'C1XW', 'CV1', 'CV1W']


CURRENTPOOL = {
    'antpool': ['etc', 'ethw'],
    'ezil': ['ezil'],
    'k1pool': ['etc'],
    '2miners': ['etc']
}


HRUNIT = {'K': 1/(1000*1000), 'M': 1/1000, 'G': 1, 'T': 1000, 'P': 1000*1000}
AVUNIT = {'K': 1000, 'M': 1000*1000, 'G': 1000*1000*1000,
          'T': 1000*1000*1000*1000, 'P': 1000*1000*1000*1000*1000}


PSU = {
    'temp_ip': '10.41.20.1',
    'power_ip': ['10.36.14.1', '10.41.20.1'],
    'port': 22,
    'username': 'root',
    'password': 'root'
}


SHOWUNIT = 'M'


POOLS = {
    "etc.f2pool.com": "etc",
    "eth.f2pool.com": "eth",
    "ethw.f2pool.com": "ethw",
    "etf.f2pool.com": "etf",
    "ethwssl.f2pool.com": "ethw",
    "etfssl.f2pool.com": "etf",
    "stratum-etc.antpool.com": "etc",
    "stratum-eth.antpool.com": "eth",
    "stratum-ethw.antpool.com": "ethw",
    "etc.ss.poolin.one": "etc",
    "eth.ss.poolin.one": "eth",
    "ethw.ss.poolin.one": "ethw",
    "etf.ss.poolin.one": "etf",
    "etc.ss.btc.com": "etc",
    "ethf.ss.btc.com": "etf",
    "8.212.2.228": "zilliqa-etc",
    'ezil.me': 'ezil',
    'etc.k1pool.com': 'etc',
    'etc.2miners.com': 'etc'
}


DEVICE_INFO = {
    'project': 'esa',
    'board': 'ipollo,nano-orgp0'
}


FIRMWARE_PATH = '/opt/benchmis/firmware/'
