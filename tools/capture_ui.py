# -*- coding: utf-8 -*-
"""
渲染主窗口 / 休息弹窗 / 设置窗口并截图（用 PrintWindow 抓窗口自身，不受遮挡影响）。
默认输出到 <项目>/screenshots/，文件名为 <语言>_<界面>.png

用法：
    python tools/capture_ui.py                  # 全部语言
    python tools/capture_ui.py --lang=en        # 只出英文
"""
import ctypes
import os
import sys
import tempfile
import time
import tkinter as tk
from ctypes import wintypes

from PIL import Image

# 必须在对 Tk 做任何事之前设置，否则量到的是被虚拟化的 96dpi 尺寸
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import i18n  # noqa: E402
import water_break_reminder as W  # noqa: E402

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
user32.GetWindowDC.restype = wintypes.HDC
user32.GetWindowDC.argtypes = [wintypes.HWND]
user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetAncestor.restype = wintypes.HWND
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT,
                            wintypes.UINT, ctypes.c_void_p,
                            ctypes.c_void_p, wintypes.UINT]
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteObject.restype = wintypes.BOOL
gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.DeleteDC.restype = wintypes.BOOL
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.ReleaseDC.restype = ctypes.c_int


class BMIH(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]


class BMI(ctypes.Structure):
    _fields_ = [("bmiHeader", BMIH), ("bmiColors", wintypes.DWORD * 3)]


def capture(win, path):
    """抓整个顶层窗口（含标题栏）"""
    win.update_idletasks()
    hwnd = user32.GetAncestor(win.winfo_id(), 2)      # GA_ROOT
    rc = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rc))
    wid, hei = rc.right - rc.left, rc.bottom - rc.top

    hdc = user32.GetWindowDC(hwnd)
    mem = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, wid, hei)
    old = gdi32.SelectObject(mem, bmp)
    user32.PrintWindow(hwnd, mem, 2)                  # PW_RENDERFULLCONTENT

    bmi = BMI()
    bmi.bmiHeader.biSize = ctypes.sizeof(BMIH)
    bmi.bmiHeader.biWidth = wid
    bmi.bmiHeader.biHeight = -hei                     # top-down
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0
    buf = ctypes.create_string_buffer(wid * hei * 4)
    gdi32.GetDIBits(mem, bmp, 0, hei, buf, ctypes.byref(bmi), 0)

    img = Image.frombuffer("RGBA", (wid, hei), buf, "raw", "BGRA",
                           0, 1).convert("RGB")
    img.save(path)
    gdi32.SelectObject(mem, old)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem)
    user32.ReleaseDC(hwnd, hdc)
    print("  %-22s %dx%d" % (os.path.basename(path), wid, hei))
    return img


def render_lang(lang, out, tip_id="hip_flexor", extra_id="chin_tuck"):
    """渲染某一个语言的三个界面并截图"""
    W.CONF_PATH = os.path.join(tempfile.gettempdir(), "wbr_shot_%s.json" % lang)
    if os.path.exists(W.CONF_PATH):
        os.remove(W.CONF_PATH)

    root = tk.Tk()
    app = W.ReminderApp(root, lang=lang)
    app.conf["sound"] = False
    app.tip_id = tip_id
    app.extra_id = extra_id

    def pump(n=14):
        for _ in range(n):
            root.update()
            time.sleep(0.04)

    pump()
    print("[%s] 字体 %s" % (lang, app.f))
    capture(root, os.path.join(out, "%s_main.png" % lang))

    app.start_break()
    pump(20)
    capture(app.break_win, os.path.join(out, "%s_break.png" % lang))

    # 休息暂停态：色条转琥珀、按钮变「继续」
    app.set_break_paused(True)
    pump(12)
    capture(app.break_win, os.path.join(out, "%s_break_paused.png" % lang))
    app.set_break_paused(False)
    pump(6)

    app.finish_break(count=False)
    pump(6)
    app.open_settings()
    pump(20)
    capture(app._set_win, os.path.join(out, "%s_settings.png" % lang))

    app.stop_ring()
    root.destroy()
    if os.path.exists(W.CONF_PATH):
        os.remove(W.CONF_PATH)


def main():
    out = os.path.join(BASE, "screenshots")
    os.makedirs(out, exist_ok=True)
    langs = [a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--lang=")]
    langs = [i18n.normalize_lang(x) for x in langs] or list(i18n.LANGS)

    for lang in langs:
        render_lang(lang, out)
    print("截图已输出到 %s" % out)


if __name__ == "__main__":
    main()
