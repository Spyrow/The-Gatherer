import ctypes
import queue
import threading
from ctypes import wintypes

WH_KEYBOARD_LL = 13
HC_ACTION = 0
LLKHF_INJECTED = 0x00000010
VK_F8 = 0x77
VK_F9 = 0x78

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", wintypes.DWORD),
                ("scanCode", wintypes.DWORD),
                ("flags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

class GlobalHotkeys:
    def __init__(self):
        self.events = queue.Queue()
        self._hook = None
        self._proc = None
        self._installed = False

    def start(self):
        if self._installed:
            return True
        try:
            self._user32 = ctypes.WinDLL("user32", use_last_error=True)
            self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            self._user32.SetWindowsHookExW.restype = wintypes.HHOOK
            self._user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC,
                                                       wintypes.HINSTANCE, wintypes.DWORD]
            self._user32.CallNextHookEx.restype = ctypes.c_long
            self._user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int,
                                                    wintypes.WPARAM, wintypes.LPARAM]
            self._user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND,
                                                 wintypes.UINT, wintypes.UINT]
            self._user32.GetMessageW.restype = wintypes.BOOL
            self._user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
            self._user32.TranslateMessage.restype = wintypes.BOOL
            self._user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
            self._user32.DispatchMessageW.restype = ctypes.c_longptr
            self._kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
            self._kernel32.GetModuleHandleW.restype = wintypes.HMODULE

            self._proc = HOOKPROC(self._callback)
            hmod = self._kernel32.GetModuleHandleW(None)
            self._hook = self._user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._proc, hmod, 0)
            if not self._hook:
                return False
            self._installed = True
            threading.Thread(target=self._pump, daemon=True).start()
            return True
        except Exception:
            return False

    def _callback(self, nCode, wParam, lParam):
        if nCode == HC_ACTION:
            kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            if kb.vkCode in (VK_F8, VK_F9) and not (kb.flags & LLKHF_INJECTED):
                self.events.put(kb.vkCode)
        return self._user32.CallNextHookEx(self._hook, nCode, wParam, lParam)

    def _pump(self):
        msg = wintypes.MSG()
        ptr = ctypes.byref(msg)
        while True:
            result = self._user32.GetMessageW(ptr, None, 0, 0)
            if result in (0, -1):
                break
            self._user32.TranslateMessage(ptr)
            self._user32.DispatchMessageW(ptr)