# -*- coding: utf-8 -*-
"""
久坐提醒助手 —— 每 45 分钟提醒你起身喝水、缓解腰部酸痛
纯 Python 标准库（tkinter），无需安装任何依赖。
双击同目录下的 start.bat 即可运行。
"""
import ctypes
import json
import os
import random
import sys
import threading
import time
import tkinter as tk
from tkinter import font as tkfont

import i18n
from i18n import EXTRA_ORDER, LANGS, LANG_NAMES, TIP_ORDER

try:
    import winreg
except ImportError:          # 非 Windows
    winreg = None

try:
    import winsound
except Exception:  # 非 Windows 环境
    winsound = None

FROZEN = bool(getattr(sys, "frozen", False))
if FROZEN:
    # PyInstaller 打包后：exe 所在目录用来放配置，资源在临时解包目录
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
    RES_DIR = getattr(sys, "_MEIPASS", APP_DIR)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    RES_DIR = APP_DIR

CONF_PATH = os.path.join(APP_DIR, "config.json")
SCRIPT_PATH = os.path.join(APP_DIR, "water_break_reminder.py")
# 开机自启真正要拉起的目标：打包后就是 exe 本身
AUTOSTART_TARGET = os.path.abspath(sys.executable) if FROZEN else SCRIPT_PATH

# 开机自启：写入 HKCU 的 Run 项，不需要管理员权限
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "WaterBreakReminder"


def autostart_exe():
    """优先用 pythonw.exe（不弹黑窗）；打包后直接就是 exe"""
    if FROZEN:
        return os.path.abspath(sys.executable)
    exe = sys.executable or "python"
    if "pythonw" not in os.path.basename(exe).lower():
        cand = os.path.join(os.path.dirname(exe), "pythonw.exe")
        if os.path.exists(cand):
            exe = cand
    return exe


def autostart_command():
    if FROZEN:
        return '"%s"' % AUTOSTART_TARGET
    return '"%s" "%s"' % (autostart_exe(), SCRIPT_PATH)


def autostart_status():
    """返回 (状态, 已注册的命令)。状态取值：on / off / stale"""
    if winreg is None:
        return "off", None
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                            winreg.KEY_READ) as k:
            val, _ = winreg.QueryValueEx(k, RUN_NAME)
    except OSError:
        return "off", None
    if not isinstance(val, str) or not val.strip():
        return "off", None
    if AUTOSTART_TARGET.lower() not in val.replace('"', " ").lower():
        return "stale", val
    return "on", val


def set_autostart(enable):
    """开启/关闭开机自启。返回 (是否成功, 说明)"""
    if winreg is None:
        return False, "当前 Python 环境不支持注册表操作"
    if enable:
        cmd = autostart_command()
        try:
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                                    winreg.KEY_SET_VALUE) as k:
                winreg.SetValueEx(k, RUN_NAME, 0, winreg.REG_SZ, cmd)
        except OSError as e:
            return False, "写入注册表失败：%s" % e
        return True, cmd
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                            winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, RUN_NAME)
    except FileNotFoundError:
        return True, "本来就是关闭状态"
    except OSError as e:
        return False, "删除注册表项失败：%s" % e
    return True, "已关闭"

# ---------------- 配色 ----------------
BG      = "#1b1d21"
CARD    = "#26292e"
CARD2   = "#31353c"
FG      = "#e8eaed"
MUTED   = "#98a2ad"
ACCENT  = "#4c9aff"
GREEN   = "#3fb950"
AMBER   = "#e3b341"
RED     = "#f85149"
BAR_W = 308                      # 主窗口进度条宽度（340 − 16×2）
HOVER = {ACCENT: "#6aabff", CARD2: "#3d424a", GREEN: "#56cc66"}

DEFAULTS = {
    "work_minutes": 45,     # 多久提醒一次
    "break_minutes": 3,     # 每次休息时长
    "snooze_minutes": 5,    # “稍后提醒”间隔
    "sound": True,          # 提示音
    "lang": None,           # 界面语言：zh / en / ja / ko（None = 跟系统）
    "pos": None,            # 主窗口位置记忆
    "stats": {},            # {"2026-09-14": {"done": 3, "skip": 0}}
}


def load_conf():
    conf = dict(DEFAULTS)
    try:
        with open(CONF_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            conf.update({k: v for k, v in data.items() if k in DEFAULTS})
            if not isinstance(conf.get("stats"), dict):
                conf["stats"] = {}
    except Exception:
        pass
    return conf


def save_conf(conf):
    try:
        with open(CONF_PATH, "w", encoding="utf-8") as f:
            json.dump(conf, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def fmt(sec):
    sec = max(0, int(sec))
    return "%02d:%02d" % (sec // 60, sec % 60)


def resolve_fonts(root, lang):
    """按界面语言挑一个系统里真实存在的字体族，避免出现豆腐块"""
    try:
        avail = set(tkfont.families(root))
    except Exception:
        avail = set()
    base = i18n.pick_font(lang, avail)
    mono = i18n.MONO_FONTS[0]
    for c in i18n.MONO_FONTS:
        if not avail or c in avail:
            mono = c
            break
    return base, mono


def round_rect(canvas, x1, y1, x2, y2, r, **kw):
    r = min(r, (x2 - x1) / 2, (y2 - y1) / 2)
    pts = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


class ReminderApp:
    def __init__(self, root, lang=None):
        self.root = root
        self.conf = load_conf()

        # DPI 缩放因子：设计稿按 96dpi 排版，这里等比放大到实际显示器
        # （字体是「点」单位会自动随 DPI 放大，所以像素尺寸也必须跟着放大，
        #   否则高缩放下窗口相对变窄，文字会大面积折行）
        try:
            self.k = max(1.0, float(root.tk.call("tk", "scaling")) / (96.0 / 72.0))
        except Exception:
            self.k = 1.0
        self.bar_w = self.P(BAR_W)

        self.state = "running"           # running / paused / break
        self.remaining = self.conf["work_minutes"] * 60
        self.break_remaining = 0
        self.break_paused = False        # 休息倒计时是否暂停（state 仍为 break）
        self.break_win = None
        self.ringing = False
        self.flash_on = False
        self.snoozed = False

        # ---- 多语言 ----
        self.lang = i18n.normalize_lang(lang or self.conf.get("lang")
                                        or i18n.detect_lang())
        self.f, self.m = resolve_fonts(root, self.lang)
        self.tip_id = random.choice(TIP_ORDER)
        self.extra_id = self.pick_extra()

        self.build_main()
        self.root.after(1000, self.tick)

    # ---------- DPI 适配 ----------
    def P(self, n):
        """把设计稿上的像素值按 DPI 等比放大"""
        return int(round(n * self.k))

    # ---------- 多语言 ----------
    def T(self, key, **kw):
        return i18n.text(self.lang, key, **kw)

    def tip_pair(self):
        return i18n.tip_text(self.lang, self.tip_id)

    def extra_pair(self):
        return i18n.extra_text(self.lang, self.extra_id)

    def tip_tag(self):
        return i18n.tag_text(self.lang, i18n.TIPS[self.tip_id]["tag"])

    def pick_extra(self):
        """抽一条“顺便”提示，避免与主动作同名"""
        main_name = i18n.tip_text(self.lang, self.tip_id)[0]
        pool = [e for e in EXTRA_ORDER
                if i18n.extra_text(self.lang, e)[0] != main_name]
        return random.choice(pool) if pool else EXTRA_ORDER[0]

    def set_lang(self, lang):
        """切换界面语言：换字体、存配置、重建界面"""
        lang = i18n.normalize_lang(lang)
        if lang == self.lang:
            return
        self.lang = lang
        self.conf["lang"] = lang
        self.f, self.m = resolve_fonts(self.root, lang)
        save_conf(self.conf)
        self.rebuild_main()
        self.break_win = None        # 弹窗按新语言下次重建

    def rebuild_main(self):
        """就地重建主窗口内容（语言/字体变化后调用）"""
        self.conf["pos"] = [self.root.winfo_x(), self.root.winfo_y()]
        for ch in self.root.winfo_children():
            ch.destroy()
        self.build_main()

    # ---------- 统计 ----------
    @property
    def today(self):
        return time.strftime("%Y-%m-%d")

    def today_stats(self):
        return self.conf["stats"].setdefault(self.today, {"done": 0, "skip": 0})

    # ---------- 主窗口 ----------
    def build_main(self):
        r = self.root
        r.title(self.T("app_title", n=self.conf["work_minutes"]))
        r.configure(bg=BG)
        r.resizable(False, False)
        r.attributes("-topmost", True)
        r.protocol("WM_DELETE_WINDOW", self.on_close)
        self.apply_icon(r, as_default=True)

        w = self.P(340)
        pos = self.conf.get("pos")
        sw, sh = r.winfo_screenwidth(), r.winfo_screenheight()

        # 顶部标题栏
        head = tk.Frame(r, bg=BG)
        head.pack(fill="x", padx=self.P(16), pady=(self.P(14), 0))
        tk.Label(head, text=self.T("app_name"), bg=BG, fg=FG,
                 font=(self.f, 12, "bold")).pack(side="left")
        self.state_dot = tk.Label(head, text=self.T("st_running"), bg=BG,
                                  fg=GREEN, font=(self.f, 9))
        self.state_dot.pack(side="right")

        # 倒计时
        self.count_lbl = tk.Label(r, text=fmt(self.remaining), bg=BG, fg=FG,
                                  font=(self.m, 42, "bold"))
        self.count_lbl.pack(pady=(self.P(12), 0))
        self.hint_lbl = tk.Label(r, text="—", bg=BG, fg=MUTED,
                                 font=(self.f, 9))
        self.hint_lbl.pack()

        # 进度条 + 语义标注
        bh = self.P(8)
        self.bar = tk.Canvas(r, width=self.bar_w, height=bh, bg=BG,
                             highlightthickness=0)
        self.bar.pack(fill="x", padx=self.P(16), pady=(self.P(14), 0))
        self.bar_bg = round_rect(self.bar, 0, 0, self.bar_w, bh, bh // 2,
                                 fill=CARD2, outline="")
        self.bar_fg = round_rect(self.bar, 0, 0, 0, bh, bh // 2,
                                 fill=ACCENT, outline="")
        barrow = tk.Frame(r, bg=BG)
        barrow.pack(fill="x", padx=self.P(16), pady=(self.P(6), 0))
        self.seated_lbl = tk.Label(barrow, text="", bg=BG, fg=MUTED,
                                   font=(self.f, 9))
        self.seated_lbl.pack(side="left")
        self.goal_lbl = tk.Label(barrow, text="", bg=BG, fg=MUTED,
                                 font=(self.f, 9))
        self.goal_lbl.pack(side="right")

        # 按钮
        btns = tk.Frame(r, bg=BG)
        btns.pack(pady=(self.P(16), 0))
        self.pause_btn = self.mkbtn(btns, self.T("btn_pause"),
                                    self.toggle_pause, ACCENT)
        self.pause_btn.pack(side="left", padx=self.P(4))
        self.mkbtn(btns, self.T("btn_break_now"), self.start_break,
                   CARD2).pack(side="left", padx=self.P(4))
        self.mkbtn(btns, self.T("btn_reset"), self.reset,
                   CARD2).pack(side="left", padx=self.P(4))

        # 底部
        foot = tk.Frame(r, bg=BG)
        foot.pack(fill="x", side="bottom", pady=(self.P(14), self.P(12)))
        self.stat_lbl = tk.Label(foot, text="", bg=BG, fg=MUTED,
                                 font=(self.f, 9))
        self.stat_lbl.pack(side="left", padx=(self.P(16), 0))
        gear = tk.Label(foot, text=self.T("settings_link"), bg=BG, fg=MUTED,
                        font=(self.f, 9), cursor="hand2")
        gear.pack(side="right", padx=(0, self.P(16)))
        gear.bind("<Button-1>", lambda e: self.open_settings())

        r.bind("<space>", self._key_pause)
        r.bind("<Escape>", lambda e: self.root.iconify())

        # 按内容定高，杜绝裁切
        r.update_idletasks()
        h = r.winfo_reqheight()
        if pos and isinstance(pos, (list, tuple)) and len(pos) == 2:
            x, y = min(max(0, pos[0]), sw - w), min(max(0, pos[1]), sh - h)
        else:
            x, y = sw - w - self.P(28), self.P(60)
        r.geometry("%dx%d+%d+%d" % (w, h, x, y))

        self.refresh_main()

    def mkbtn(self, parent, text, cmd, color):
        """扁平按钮 + 悬停反馈"""
        hover = HOVER.get(color, color)
        b = tk.Button(parent, text=text, command=cmd, bg=color, fg="#ffffff",
                      activebackground=color, activeforeground="#ffffff",
                      font=(self.f, 9), relief="flat", bd=0, cursor="hand2",
                      takefocus=0, padx=self.P(14), pady=self.P(7))
        b.bind("<Enter>", lambda e: b.config(bg=hover))
        b.bind("<Leave>", lambda e: b.config(bg=color))
        return b

    def apply_icon(self, win, as_default=False):
        """套用 app.ico（缺失就跳过）"""
        ico = os.path.join(RES_DIR, "app.ico")
        if not os.path.exists(ico):
            return
        try:
            if as_default:
                win.iconbitmap(default=ico)
            else:
                win.iconbitmap(ico)
        except Exception:
            pass

    # ---------- 刷新主界面 ----------
    def refresh_main(self):
        bp = (self.state == "break" and self.break_paused)
        if self.state == "break":
            self.count_lbl.config(text=fmt(self.break_remaining),
                                  fg=AMBER if bp else GREEN)
            self.hint_lbl.config(text=self.T("paused_hint") if bp
                                 else self.T("break_hint"))
            self.state_dot.config(text=self.T("st_paused") if bp
                                  else self.T("st_break"),
                                  fg=AMBER if bp else GREEN)
        else:
            self.count_lbl.config(text=fmt(self.remaining),
                                  fg=MUTED if self.state == "paused" else FG)
            if self.state == "paused":
                self.hint_lbl.config(text=self.T("paused_hint"))
                self.state_dot.config(text=self.T("st_paused"), fg=AMBER)
            else:
                nxt = time.strftime("%H:%M",
                                    time.localtime(time.time() + self.remaining))
                self.hint_lbl.config(text=self.T("next_at", t=nxt))
                self.state_dot.config(text=self.T("st_running"), fg=GREEN)
        # 休息暂停时，主窗口的按钮也要显示「继续」
        self.pause_btn.config(text=self.T("btn_resume")
                              if (self.state == "paused" or bp)
                              else self.T("btn_pause"))

        total = max(1, self.conf["work_minutes"] * 60)
        seated = int(round((total - max(0, self.remaining)) / 60.0))
        if self.state == "break":
            ratio, seated = 1.0, self.conf["work_minutes"]
        else:
            ratio = 1.0 - min(1.0, max(0.0, self.remaining / total))
        self.bar.coords(self.bar_fg,
                        *self._rect_pts(self.bar_w * ratio, self.P(8), self.P(4)))
        if bp:
            color = AMBER
        elif self.state == "break":
            color = GREEN
        elif self.state == "paused":
            color = AMBER
        else:
            color = ACCENT
        self.bar.itemconfig(self.bar_fg, fill=color)
        self.seated_lbl.config(text=self.T("seated", n=seated))
        self.goal_lbl.config(text=self.T("goal", n=self.conf["work_minutes"]))

        s = self.today_stats()
        self.stat_lbl.config(text=self.T("stat", a=s["done"], b=s["skip"]))

    @staticmethod
    def _rect_pts(x2, h, r):
        x1, y1, y2 = 0, 0, h
        if x2 < 2 * r:
            return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        return [

            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        ]

    # ---------- 计时 ----------
    def tick(self):
        if self.state == "running":
            self.remaining -= 1
            if self.remaining <= 0:
                self.start_break()
        elif self.state == "break":
            if not self.break_paused:
                self.break_remaining -= 1
                if self.break_win and self.break_win.winfo_exists():
                    self.break_lbl.config(text=fmt(self.break_remaining))
                    self.update_break_bar()
                    if self.break_remaining <= 0:
                        self.finish_break(count=True)
        self.refresh_main()
        self.root.after(1000, self.tick)

    def toggle_pause(self):
        if self.state == "running":
            self.state = "paused"
        elif self.state == "paused":
            self.state = "running"
        elif self.state == "break":
            self.set_break_paused(not self.break_paused)
            return
        self.refresh_main()

    def _key_pause(self, event):
        """空格 = 暂停/继续。

        点击 Tk 按钮会让它拿到焦点，此时空格会被 Button 的类绑定先消费掉一次；
        这里再判一遍 event.widget，避免同一次按键触发两遍（连按两下等于没按）。
        """
        if isinstance(event.widget, tk.Button):
            return
        self.toggle_pause()

    def set_break_paused(self, on):
        """暂停/继续休息倒计时（弹窗与主窗口的暂停按钮都走这里）"""
        if self.state != "break":
            return
        self.break_paused = bool(on)
        if self.break_paused:
            self.stop_ring()             # 已确认，先安静下来，别一直响
        self._sync_break_ui()
        self.refresh_main()

    def _sync_break_ui(self):
        """把暂停状态同步到休息弹窗（倒计时配色、标签、按钮文案、顶部色条）"""
        w = self.break_win
        if not (w and w.winfo_exists()):
            return
        if self.break_paused:
            self.break_lbl.config(fg=AMBER)
            self.break_state_lbl.config(text=self.T("break_paused"), fg=AMBER)
            self.break_pause_btn.config(text=self.T("btn_resume"))
            self.banner.config(bg=AMBER)
        else:
            self.break_lbl.config(fg=GREEN)
            self.break_state_lbl.config(text=self.T("countdown"), fg=MUTED)
            self.break_pause_btn.config(text=self.T("btn_pause"))
            self.banner.config(bg=ACCENT)

    def reset(self):
        if self.state != "break":
            self.state = "running"
            self.remaining = self.conf["work_minutes"] * 60
        self.refresh_main()

    # ---------- 休息弹窗 ----------
    def start_break(self, manual=True):
        if self.state == "break":
            return
        self.state = "break"
        self.break_remaining = self.conf["break_minutes"] * 60
        self.break_paused = False
        self.tip_id = random.choice(TIP_ORDER)
        self.extra_id = self.pick_extra()
        self.snoozed = False

        w = tk.Toplevel(self.root)
        self.break_win = w
        w.title(self.T("win_break"))
        w.configure(bg=BG)
        w.resizable(False, False)
        w.attributes("-topmost", True)
        w.withdraw()                       # 先隐藏，排完版再显示，避免尺寸跳动
        w.protocol("WM_DELETE_WINDOW", lambda: self.delay_break(skip=False))

        W = self.P(520)
        PAD = self.P(22)
        inner = W - PAD * 2                # 卡片外宽
        text_w = inner - self.P(40)        # 卡片内文字换行宽度
        self.break_inner = inner

        self.banner = tk.Frame(w, bg=ACCENT, height=self.P(5))
        self.banner.pack(fill="x")

        # ---- 标题 ----
        head = tk.Frame(w, bg=BG)
        head.pack(fill="x", pady=(self.P(20), 0))
        tk.Label(head, text=self.T("break_title"), bg=BG, fg=FG,
                 font=(self.f, 18, "bold")).pack()
        tk.Label(head, text=self.T("break_sub", n=self.conf["work_minutes"]),
                 bg=BG, fg=MUTED, font=(self.f, 10)).pack(pady=(self.P(4), 0))

        # ---- 卡片（左侧色条 + 标签/名称 + 说明） ----
        def card(tag_label, tag_color, name, desc, top_pad):
            outer = tk.Frame(w, bg=CARD)
            outer.pack(fill="x", padx=PAD, pady=(self.P(top_pad), 0))
            tk.Frame(outer, bg=tag_color, width=self.P(3)).pack(side="left",
                                                               fill="y")
            body = tk.Frame(outer, bg=CARD)
            body.pack(side="left", fill="both", expand=True,
                      padx=(self.P(14), self.P(16)), pady=self.P(12))
            row = tk.Frame(body, bg=CARD)
            row.pack(fill="x")
            tk.Label(row, text=tag_label, bg=CARD, fg=tag_color,
                     font=(self.f, 10, "bold")).pack(side="left")
            if name:
                tk.Label(row, text=name, bg=CARD, fg=FG,
                         font=(self.f, 11, "bold")).pack(side="right")
            tk.Label(body, text=desc, bg=CARD, fg=FG, font=(self.f, 12),
                     wraplength=text_w, justify="left", anchor="w").pack(
                         fill="x", pady=(self.P(5), 0))
            return outer

        card(self.T("step1"), ACCENT, self.T("water_amount"),
             self.T("water_desc"), 18)
        name, desc = self.tip_pair()
        card(self.T("step2", tag=self.tip_tag()), GREEN, name, desc, 10)

        # ---- 顺便（低层级提示，用描边弱化） ----
        extra_box = tk.Frame(w, bg=BG, highlightbackground=CARD2,
                             highlightthickness=1)
        extra_box.pack(fill="x", padx=PAD, pady=(self.P(10), 0))
        tk.Label(extra_box, text=self.T("extra", name=self.extra_pair()[0]),
                 bg=BG, fg=MUTED,
                 font=(self.f, 10, "bold")).pack(anchor="w", padx=self.P(14),
                                               pady=(self.P(9), 0))
        tk.Label(extra_box, text=self.extra_pair()[1], bg=BG, fg=MUTED,
                 font=(self.f, 10), wraplength=text_w, justify="left",
                 anchor="w").pack(fill="x", padx=self.P(14),
                                  pady=(self.P(3), self.P(9)))

        # ---- 倒计时 ----
        cd = tk.Frame(w, bg=BG)
        cd.pack(fill="x", pady=(self.P(18), 0))
        self.break_state_lbl = tk.Label(cd, text=self.T("countdown"), bg=BG,
                                        fg=MUTED, font=(self.f, 10))
        self.break_state_lbl.pack()
        self.break_lbl = tk.Label(cd, text=fmt(self.break_remaining), bg=BG,
                                  fg=GREEN, font=(self.m, 28, "bold"))
        self.break_lbl.pack(pady=(self.P(2), 0))

        bh = self.P(6)
        self.break_bar = tk.Canvas(w, width=inner, height=bh, bg=BG,
                                   highlightthickness=0)
        self.break_bar.pack(pady=(self.P(10), 0))
        round_rect(self.break_bar, 0, 0, inner, bh, bh // 2, fill=CARD2,
                   outline="")
        self.break_bar_fg = round_rect(self.break_bar, 0, 0, 0, bh, bh // 2,
                                       fill=GREEN, outline="")

        # ---- 按钮 ----
        btns = tk.Frame(w, bg=BG)
        btns.pack(pady=(self.P(20), self.P(22)))
        self.mkbtn(btns, self.T("btn_done"), lambda: self.finish_break(True),
                   GREEN).pack(side="left", padx=self.P(4))
        # 休息也能暂停：中途被叫走时把倒计时停住，回来再继续
        self.break_pause_btn = self.mkbtn(btns, self.T("btn_pause"),
                                          self.toggle_pause, ACCENT)
        self.break_pause_btn.pack(side="left", padx=self.P(4))
        self.mkbtn(btns, self.T("btn_snooze", n=self.conf["snooze_minutes"]),
                   lambda: self.delay_break(False),
                   CARD2).pack(side="left", padx=self.P(4))
        self.mkbtn(btns, self.T("btn_skip"), lambda: self.delay_break(True),
                   CARD2).pack(side="left", padx=self.P(4))

        w.bind("<Return>", lambda e: self.finish_break(True))
        w.bind("<space>", self._key_pause)
        w.bind("<Escape>", lambda e: self.delay_break(False))

        # ---- 按实际内容定高，保证不裁切 ----
        w.update_idletasks()
        H = min(w.winfo_reqheight(), w.winfo_screenheight() - self.P(90))
        sw, sh = w.winfo_screenwidth(), w.winfo_screenheight()
        w.geometry("%dx%d+%d+%d" % (W, H, (sw - W) // 2, max(0, (sh - H) // 3)))
        w.deiconify()
        w.lift()
        w.focus_force()
        self.refresh_main()
        self.update_break_bar()
        self._sync_break_ui()

        self.start_ring()

    def update_break_bar(self):
        if not (self.break_win and self.break_win.winfo_exists()):
            return
        total = max(1, self.conf["break_minutes"] * 60)
        ratio = 1.0 - min(1.0, max(0.0, self.break_remaining / total))
        try:
            self.break_bar.coords(
                self.break_bar_fg,
                *self._rect_pts(getattr(self, "break_inner", self.P(476)) * ratio,
                                self.P(6), self.P(3)))
        except Exception:
            pass

    # ---------- 提示音 + 闪烁 ----------
    def start_ring(self):
        if self.ringing:
            return
        self.ringing = True
        if self.conf.get("sound", True):
            t = threading.Thread(target=self._ring_loop, daemon=True)
            t.start()

    def _ring_loop(self):
        start = time.time()
        while self.ringing:
            if winsound:
                try:
                    winsound.Beep(880, 170)
                    time.sleep(0.10)
                    winsound.Beep(1180, 170)
                except Exception:
                    pass
            gap = 0.9 if time.time() - start < 15 else 4.0
            time.sleep(gap)

    def stop_ring(self):
        self.ringing = False

    def _flash(self):
        if not (self.break_win and self.break_win.winfo_exists()):
            return
        if self.break_paused:
            # 暂停时色条保持琥珀色常亮，不闪烁
            try:
                self.banner.config(bg=AMBER)
            except Exception:
                return
            self.root.after(600, self._flash)
            return
        self.flash_on = not self.flash_on
        try:
            self.banner.config(bg=ACCENT if self.flash_on else CARD2)
            if self.ringing:
                self.break_win.lift()
                self.break_win.attributes("-topmost", True)
        except Exception:
            return
        self.root.after(600, self._flash)

    # ---------- 结束 / 延后 ----------
    def finish_break(self, count=True):
        self.stop_ring()
        self.close_break_win()
        self.break_paused = False
        if count:
            self.today_stats()["done"] += 1
        self.state = "running"
        self.remaining = self.conf["work_minutes"] * 60
        save_conf(self.conf)
        self.refresh_main()

    def delay_break(self, skip=True):
        self.stop_ring()
        self.close_break_win()
        self.break_paused = False
        if skip:
            self.today_stats()["skip"] += 1
            delay = self.conf["work_minutes"] * 60 - self.conf["snooze_minutes"] * 60
            delay = max(60, delay)
        else:
            delay = self.conf["snooze_minutes"] * 60
        self.state = "running"
        self.remaining = delay
        save_conf(self.conf)
        self.refresh_main()

    def close_break_win(self):
        w = self.break_win
        self.break_win = None
        if w is not None:
            try:
                if w.winfo_exists():
                    w.grab_release()
                    w.destroy()
            except Exception:
                pass

    # ---------- 设置窗口 ----------
    def open_settings(self):
        if getattr(self, "_set_win", None) and self._set_win.winfo_exists():
            self._set_win.lift()
            return
        w = tk.Toplevel(self.root)
        self._set_win = w
        w.title(self.T("win_settings"))
        w.configure(bg=BG)
        w.resizable(False, False)
        w.attributes("-topmost", True)
        w.withdraw()

        PAD = self.P(20)
        tk.Label(w, text=self.T("set_title"), bg=BG, fg=FG,
                 font=(self.f, 12, "bold")).pack(anchor="w", padx=PAD,
                                                 pady=(self.P(16), self.P(2)))
        tk.Label(w, text=self.T("set_sub"), bg=BG, fg=MUTED,
                 font=(self.f, 9)).pack(anchor="w", padx=PAD)
        tk.Frame(w, bg=CARD2, height=1).pack(fill="x", padx=PAD,
                                             pady=(self.P(12), 0))

        v1 = tk.IntVar(value=self.conf["work_minutes"])
        v2 = tk.IntVar(value=self.conf["break_minutes"])
        v3 = tk.IntVar(value=self.conf["snooze_minutes"])
        v4 = tk.BooleanVar(value=bool(self.conf.get("sound", True)))

        def row(label, var, lo, hi):
            f = tk.Frame(w, bg=BG)
            f.pack(fill="x", padx=PAD, pady=(self.P(11), 0))
            tk.Label(f, text=label, bg=BG, fg=FG, font=(self.f, 10),
                     width=10, anchor="w").pack(side="left")
            tk.Spinbox(f, from_=lo, to=hi, textvariable=var, width=5,
                       font=(self.f, 10), bg=CARD2, fg=FG, relief="flat",
                       buttonbackground=CARD2, justify="center",
                       insertbackground=FG, takefocus=0).pack(side="left")
            tk.Label(f, text=self.T("unit_min"), bg=BG, fg=MUTED,
                     font=(self.f, 9)).pack(side="left", padx=(self.P(8), 0))

        row(self.T("set_interval"), v1, 1, 240)
        row(self.T("set_duration"), v2, 1, 30)
        row(self.T("set_snooze"), v3, 1, 60)

        # ---- 界面语言（点了立即切换，实时预览） ----
        lrow = tk.Frame(w, bg=BG)
        lrow.pack(fill="x", padx=PAD, pady=(self.P(13), 0))
        tk.Label(lrow, text=self.T("set_language"), bg=BG, fg=FG,
                 font=(self.f, 10), width=10, anchor="w").pack(side="left")
        chips = tk.Frame(lrow, bg=BG)
        chips.pack(side="left")
        for code in LANGS:
            on = (code == self.lang)
            chip = tk.Label(chips, text=LANG_NAMES[code],
                            bg=ACCENT if on else CARD2,
                            fg="#ffffff" if on else MUTED,
                            font=(self.f, 9), cursor="hand2",
                            padx=self.P(10), pady=self.P(4))
            chip.pack(side="left", padx=(0, self.P(6)))
            chip.bind("<Button-1>",
                      lambda e, c=code: self._switch_lang(c, w, commit))

        ck = tk.Frame(w, bg=BG)
        ck.pack(fill="x", padx=PAD, pady=(self.P(12), 0))
        tk.Checkbutton(ck, text=self.T("set_sound"), variable=v4, bg=BG, fg=FG,
                       selectcolor=CARD2, activebackground=BG,
                       activeforeground=FG, font=(self.f, 10),
                       takefocus=0).pack(anchor="w")

        # ---- 开机自启 ----
        st, _registered = autostart_status()
        v5 = tk.BooleanVar(value=(st == "on"))
        ck2 = tk.Frame(w, bg=BG)
        ck2.pack(fill="x", padx=PAD, pady=(self.P(6), 0))
        tk.Checkbutton(ck2, text=self.T("set_autostart"), variable=v5, bg=BG,
                       fg=FG, selectcolor=CARD2, activebackground=BG,
                       activeforeground=FG, font=(self.f, 10),
                       takefocus=0).pack(anchor="w")
        auto_hint = tk.Label(
            w, text=self.T("autostart_hint"), bg=BG, fg=MUTED,
            font=(self.f, 9), justify="left",
            anchor="w", wraplength=self.P(320))
        auto_hint.pack(fill="x", padx=PAD, pady=(self.P(3), 0))
        if st == "stale":
            auto_hint.config(text=self.T("autostart_stale"), fg=AMBER)

        def safe_int(var, lo, hi, default):
            try:
                return max(lo, min(hi, int(float(var.get()))))
            except Exception:
                return default

        def commit():
            """把数值项落盘（语言切换前也要先保住用户刚改的数字）"""
            self.conf["work_minutes"] = safe_int(v1, 1, 240, 45)
            self.conf["break_minutes"] = safe_int(v2, 1, 30, 3)
            self.conf["snooze_minutes"] = safe_int(v3, 1, 60, 5)
            self.conf["sound"] = bool(v4.get())
            save_conf(self.conf)

        def do_save():
            commit()
            self.reset()

            want = bool(v5.get())
            cur, _ = autostart_status()
            if want != (cur == "on"):
                ok, msg = set_autostart(want)
                if not ok:
                    auto_hint.config(text=self.T("autostart_fail", msg=msg),
                                     fg=RED)
                    return
            w.destroy()

        btns = tk.Frame(w, bg=BG)
        btns.pack(fill="x", padx=PAD, pady=(self.P(18), self.P(16)))
        self.mkbtn(btns, self.T("save"), do_save, ACCENT).pack(
            side="right", padx=(self.P(6), 0))
        self.mkbtn(btns, self.T("cancel"), w.destroy, CARD2).pack(side="right")
        link = tk.Label(btns, text=self.T("restore"), bg=BG, fg=MUTED,
                        font=(self.f, 9), cursor="hand2")
        link.pack(side="left")
        link.bind("<Button-1>", lambda e: (v1.set(45), v2.set(3), v3.set(5),
                                           v4.set(True)))

        w.bind("<Return>", lambda e: do_save())
        w.bind("<Escape>", lambda e: w.destroy())

        # 按内容定尺寸，并保证不跑出屏幕
        w.update_idletasks()
        W_ = max(self.P(320), w.winfo_reqwidth())
        H_ = w.winfo_reqheight()
        sw, sh = w.winfo_screenwidth(), w.winfo_screenheight()
        x = self.root.winfo_x() - W_ - self.P(12)
        if x < 0:
            x = self.root.winfo_x() + self.root.winfo_width() + self.P(12)
        x = min(max(0, x), max(0, sw - W_))
        y = min(max(0, self.root.winfo_y()), max(0, sh - H_))
        w.geometry("%dx%d+%d+%d" % (W_, H_, x, y))
        w.deiconify()
        w.lift()
        w.focus_force()

    def _switch_lang(self, code, set_win, commit=None):
        """切换语言并就地重建设置窗口（实时预览）"""
        if i18n.normalize_lang(code) == self.lang:
            return
        if commit:
            commit()                     # 先保住用户刚改的数字
        self.set_lang(code)
        if set_win is not None:
            try:
                if set_win.winfo_exists():
                    set_win.destroy()
            except Exception:
                pass
        self.open_settings()

    # ---------- 关闭 ----------
    def on_close(self):
        self.stop_ring()
        self.conf["pos"] = [self.root.winfo_x(), self.root.winfo_y()]
        save_conf(self.conf)
        self.root.destroy()


def main():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    args = [a for a in sys.argv[1:] if a.startswith("--lang=")]
    lang_arg = args[0].split("=", 1)[1] if args else None

    selftest = "--selftest" in sys.argv
    root = tk.Tk()
    app = ReminderApp(root, lang=lang_arg)

    if selftest:
        # 走一遍完整排版路径（含最复杂的休息弹窗），并断言内容没被裁切
        app.conf["sound"] = False
        app.start_break()
        for _ in range(8):
            root.update()
            time.sleep(0.03)
        bw = app.break_win
        bw.update_idletasks()
        bh = bw.winfo_height()
        kids = bw.winfo_children()
        bottom = kids[-1].winfo_y() + kids[-1].winfo_height() if kids else 0
        ok = bool(kids) and bottom <= bh
        print("自检%s：[%s] 主窗 %dx%d，弹窗 %dx%d（按钮底边 %d），"
              "动作库 %d 条，自启 %s"
              % ("通过" if ok else "失败（弹窗内容被裁切）", app.lang,
                 root.winfo_width(), root.winfo_height(),
                 bw.winfo_width(), bh, bottom,
                 len(i18n.TIP_ORDER), autostart_status()[0]))
        if not ok:
            print("（提示：内容被裁切，请检查该语言的文案长度）")
        app.stop_ring()
        root.destroy()
        return 0 if ok else 1

    app._flash()
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
