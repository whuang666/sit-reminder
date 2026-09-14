# -*- coding: utf-8 -*-
"""
穷举排版校验（多语言版）
对 4 种语言 × 13 个主动作 × 4 条顺便提示 = 208 种组合逐一渲染休息弹窗，检查：
  1) 纵向：最底部控件底边不超过客户区高度
  2) 横向：任一后代控件的右边缘不超过客户区宽度（多语言文案更长，最容易在这里溢出）
另外用最长文案压一遍主窗口，检查横向溢出。
用法：python tools/verify_layout.py
"""
import ctypes
import os
import sys
import tempfile
import time
import tkinter as tk

# 必须在对 Tk 做任何事之前设置
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import i18n  # noqa: E402
import water_break_reminder as W  # noqa: E402

W.CONF_PATH = os.path.join(tempfile.gettempdir(), "wbr_verify_conf.json")
if os.path.exists(W.CONF_PATH):
    os.remove(W.CONF_PATH)


def overflow_widgets(win, w, h):
    """找出越过客户区边界的后代控件（用根坐标换算，避开相对坐标的坑）"""
    bad = []
    ox, oy = win.winfo_rootx(), win.winfo_rooty()

    def walk(widget):
        for ch in widget.winfo_children():
            ch.update_idletasks()
            right = ch.winfo_rootx() - ox + ch.winfo_width()
            bottom = ch.winfo_rooty() - oy + ch.winfo_height()
            if right > w + 1 or bottom > h + 1:
                try:
                    label = ch.cget("text")
                except Exception:
                    label = ""
                bad.append((ch.winfo_class(), str(label)[:28], right, bottom))
            walk(ch)

    walk(win)
    return bad


def pump(root, n=5):
    for _ in range(n):
        root.update()
        time.sleep(0.012)


def check_popups(lang):
    """某一语言下的全部动作组合 -> (通过数, 总数, 失败明细, 字体, 弹窗宽)"""
    root = tk.Tk()
    app = W.ReminderApp(root, lang=lang)
    app.conf["sound"] = False
    ok, fails = 0, []
    n = len(i18n.TIP_ORDER) * len(i18n.EXTRA_ORDER)

    for tid in i18n.TIP_ORDER:
        for eid in i18n.EXTRA_ORDER:
            app.lang = lang
            app.tip_id = tid
            app.extra_id = eid
            app.state = "running"
            app.start_break()
            pump(root)
            bw = app.break_win
            bw.update_idletasks()
            Wc, Hc = bw.winfo_width(), bw.winfo_height()
            kids = bw.winfo_children()
            bottom = (kids[-1].winfo_rooty() - bw.winfo_rooty()
                      + kids[-1].winfo_height()) if kids else 0
            bad = overflow_widgets(bw, Wc, Hc)

            if bottom > Hc or bad:
                fails.append((tid, eid, Wc, Hc, bottom, bad[:3]))
            else:
                ok += 1

            app.finish_break(count=False)
            pump(root, 2)
            app.state = "running"

    info = (ok, n, fails, app.f, app.P(520))
    app.stop_ring()
    root.destroy()
    return info


def check_main(lang):
    """主窗口：用最长文案压一遍，只看横向溢出"""
    root = tk.Tk()
    app = W.ReminderApp(root, lang=lang)
    app.conf["sound"] = False
    app.conf["work_minutes"] = 240
    app.state = "running"
    app.remaining = 60
    app.today_stats()["done"] = 99
    app.today_stats()["skip"] = 99
    app.refresh_main()
    pump(root, 8)
    Wm, Hm = root.winfo_width(), root.winfo_height()
    hbad = [b for b in overflow_widgets(root, Wm, Hm) if b[2] > Wm + 1]
    app.stop_ring()
    root.destroy()
    return Wm, Hm, hbad


total, all_fails = 0, []
for lang in i18n.LANGS:
    ok, n, fails, font, bw = check_popups(lang)
    total += n
    all_fails += [(lang,) + f for f in fails]
    print("%-3s %-8s 弹窗 %2d/%d   字体 %-18s 弹窗宽 %d px"
          % (lang, i18n.LANG_NAMES[lang], ok, n, font, bw))

print()
print("弹窗组合总数 %d，异常 %d" % (total, len(all_fails)))
if all_fails:
    for f in all_fails:
        print("  裁切:", f)
    sys.exit(1)

print()
worst = 0
for lang in i18n.LANGS:
    Wm, Hm, hbad = check_main(lang)
    print("%-3s 主窗 %dx%d   横向溢出 %d %s"
          % (lang, Wm, Hm, len(hbad), hbad[:2] if hbad else ""))
    worst += len(hbad)

print()
if worst:
    print("主窗口存在横向溢出 ✘")
    sys.exit(1)
print("排版校验通过 ✔（4 语言 × 17 种文案组合，全部不裁切、不溢出）")
if os.path.exists(W.CONF_PATH):
    os.remove(W.CONF_PATH)
