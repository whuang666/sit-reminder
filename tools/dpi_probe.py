# -*- coding: utf-8 -*-
"""DPI / 缩放诊断：对比「控制台启动」与「pythonw 直接启动」两种模式。"""
import ctypes
import os
import subprocess
import sys
import tkinter as tk

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(os.path.dirname(HERE), "water_break_reminder.py")


def probe():
    r = tk.Tk()
    r.withdraw()
    sw, sh = r.winfo_screenwidth(), r.winfo_screenheight()
    scaling = float(r.tk.call("tk", "scaling"))
    print("sys.executable      :", os.path.basename(sys.executable))
    print("tk scaling          : %.4f" % scaling)
    print("推算 DPI            : %.1f" % (scaling * 72))
    print("screen              : %d x %d" % (sw, sh))
    print("winfo_fpixels('1i') : %.1f" % r.winfo_fpixels("1i"))
    print("=> 布局缩放系数 k   : %.3f" % max(1.0, scaling / (96.0 / 72.0)))
    r.destroy()


def probe_aware():
    try:
        rc = ctypes.windll.shcore.SetProcessDpiAwareness(1)
        print("SetProcessDpiAwareness 返回:", rc, "(0=S_OK, 0x80070005=已设置过)")
    except Exception as e:
        print("SetProcessDpiAwareness 失败:", e)
    probe()


if __name__ == "__main__":
    if "--child" in sys.argv:
        probe_aware()
        sys.exit(0)

    print("========== A) 控制台启动（不做 DPI 设置） ==========")
    probe()
    print()
    print("========== B) 控制台启动 + 显式设置 DPI 感知 ==========")
    probe_aware()
    print()
    print("========== C) pythonw 直接启动（等同双击 start.bat） ==========")
    pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(pyw):
        pyw = sys.executable
    r = subprocess.run([pyw, __file__, "--child"], capture_output=True,
                       encoding="utf-8", errors="replace", timeout=90,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    print((r.stdout or "").strip() or "(无输出)")
    if r.stderr and r.stderr.strip():
        print("stderr:", r.stderr.strip()[:400])
