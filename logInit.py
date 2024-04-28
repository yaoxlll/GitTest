import logging
from logging.handlers import RotatingFileHandler
import settings
import datetime
import pytz

class TimezoneRotatingFileHandler(RotatingFileHandler):
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=False):
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)

    # 重写 emit 方法，在记录日志时将时间转换为指定时区的时间
    def emit(self, record):
        tz = pytz.timezone(settings.TIME_ZONE)  # 获取时区设置
        record.asctime = datetime.datetime.fromtimestamp(record.created, tz).strftime('%Y-%m-%d %H:%M:%S %Z')
        super().emit(record)