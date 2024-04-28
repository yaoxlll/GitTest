import ctypes
from enum import Enum


class encrypt_algos(Enum):
    ALGO_MD5 = 0
    ALGO_SHA1 = 1
    ALGO_SHA256 = 2
    ALGO_SHA512 = 3
    ALGO_RC4C = 4

class GenPwdContext(ctypes.Structure):
    _fields_ = [
        #(字段名, c类型 )
        ( 'algo',       ctypes.c_uint8 ),
        ( 'cbsn',       ctypes.c_char_p ),
        ( 'cbsn_len',   ctypes.c_uint8 ),
        ( 'cpuid',      ctypes.c_char_p),
        ( 'cpuid_len',  ctypes.c_uint8 ),
        ( 'pos',        ctypes.c_uint8 ),
        ( 'length',     ctypes.c_uint8 ),
        ( 'passwd',     ctypes.c_char_p)
    ]
iPolloCrypt = ctypes.CDLL('./v/libiPolloCrypt.so.0.1')
iPolloCrypt.libgenpwd.restype = ctypes.c_int

def testlib(cbsn: str, cpuid: str):
    # Use a breakpoint in the code line below to debug your script.
    # cbsn = input("input CBSN:")
    # cpuid = input("input CPUID:")
    ctx = GenPwdContext()
    if cbsn:
        ctx.cbsn = ctypes.c_char_p(cbsn.encode())
        
    ctx.cbsn_len = len(ctx.cbsn)
    ctx.cpuid = ctypes.c_char_p(cpuid.encode())
    ctx.cpuid_len = len(ctx.cpuid)
    ctx.pos = 7
    ctx.length = 8
    ctx.algo = encrypt_algos.ALGO_SHA256.value
    res = iPolloCrypt.libgenpwd(ctypes.pointer(ctx))
    if res:
        return None
    else:
        return str(ctx.passwd,encoding="utf-8")
