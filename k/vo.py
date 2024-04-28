from dataclasses import dataclass


@dataclass
class ApiData:
    name: str = None
    scan_ip: str = None

    sn: str = None
    miner_sn: str = None
    model: str = None
    hw_type: str = None
    sw_type: str = None
    version: str = None
    os_version: str = None
    fpga_version: str = None
    cb: str = None
    mac: str = None
    api_ip: str = None
    gateway: str = None
    mask: str = None
    vx: str = None
    psu_model: str = None
    psu_serial: str = None

    when: int = None
    elapsed: int = None
    pool_url: str = None
    pool_user: str = None
    pool1_url: str = None
    pool1_user: str = None
    pool2_url: str = None
    pool2_user: str = None
    pool3_url: str = None
    pool3_user: str = None

    vout: int = None
    iout: int = None
    pout: int = None
    psu_ver: str = None
    psu_err: int = None
    g_status: str = None
    r_status: str = None
    g_interval: int = None
    r_interval: int = None
    round_speed: list = None
    fan_speed: list = None
    red_led: str = None
    c_temp: float = None
    uptm: str = None
    hr_local: float = None
    
    instru_v: float = None
    instru_i: float = None
    instru_ap: float = None
    env_temp: float = None
    env_humi: float = None
    coin_type: str = None
    hr_unit: str = None
  
    hr_pool: float = None
    hr_pool_1h: float = None
    hr_pool_24h: float = None
    reject_rate_pool: float = None
    
    chips: dict = None
    datas: dict = None
    cores: dict = None
    memo: dict = None
    mempll: dict = None
    mode: dict = None
    boost: dict = None

    extra_cmds: dict = None
    