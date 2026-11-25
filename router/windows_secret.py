import ctypes
from ctypes import wintypes
import os
from pathlib import Path


def app_data_root():
    return Path(os.environ.get('LOCALAPPDATA') or Path.home() / 'AppData/Local') / 'AidolEventRouter'


def protect(data, decrypt=False):
    if os.name != 'nt':
        raise RuntimeError('Event Router MCP currently supports Windows only')
    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_byte))]
    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    result = Blob()
    library = ctypes.WinDLL('crypt32', use_last_error=True)
    function = library.CryptUnprotectData if decrypt else library.CryptProtectData
    function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                         ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    function.restype = wintypes.BOOL
    if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(result)):
        raise RuntimeError('Cannot read local connection credential under this Windows account')
    try:
        return ctypes.string_at(result.data, result.size)
    finally:
        free = ctypes.WinDLL('kernel32', use_last_error=True).LocalFree
        free.argtypes = [ctypes.c_void_p]
        free(ctypes.cast(result.data, ctypes.c_void_p))
