from dataclasses import dataclass


@dataclass
class ApiData:
    miner_sn: str = None
    model: str = None
    hw_type: str = None
    sw_type: str = None
    version: str = None
    os_version:str  = None
    firmware_version = None
    bit_link: str = None
    mac: str = None
    powersn: str = None
    psu_model: str = None
    psu_serial: str = None
    vx: str = None
    coin_type: str = None
    lot_id: str = None
    cpid: str = None

    api_ip: str = None
    scan_ip: str = None
    gateway: str = None
    mask: str = None

    hbsn: dict = None
    hbtemp: list = None
    hbfreq: list = None

    vout: int = None
    iout: int = None
    pout: int = None
    psu_ver: str = None
    psu_err: int = None
    g_status: str = None
    r_status: str = None
    g_interval: str = None
    fan_speed: list = None
    c_temp: float = None
    uptm: float = None

    instru_v: float = None
    instru_i: float = None
    instru_ap: float = None
    env_temp: float = None
    env_humi: float = None

    when: int = None
    elapsed: int = None
    accepted_local: float = None
    accepted_local_g: float = None
    hr_local: float = None
    hr_local_1m: float = None
    hr_local_5m: float = None
    hr_local_15m: float = None
    hr_local_g: float = None
    hr_local_1m_g: float = None
    hr_local_5m_g: float = None
    hr_local_15m_g: float = None
    hr_pool: float = None
    hr_pool_1h: float = None
    hr_pool_24h: float = None
    hr_pool_g: float = None
    hr_pool_1h_g: float = None
    hr_pool_24h_g: float = None
    hr_unit: str = None

    reject_rate_pool: float = None
    reject_rate_local: float = None
    pool_url: str = None
    pool_user: str = None
    pool1_url: str = None
    pool1_user: str = None
    pool2_url: str = None
    pool2_user: str = None
    pool3_url: str = None
    pool3_user: str = None
    
    power_consume: float = None
    pe_pool: float = None
    pe_pool_g: float = None
    pe_local: float = None
    pe_local_g: float = None
    
    chips: dict = None
    datas: dict = None
    cores: dict = None
    extra_cmds: dict = None
    error_msg: dict = None
