# -*- coding: utf-8 -*-
"""冒烟测试：不进入 mainloop，手动触发计时/弹窗/结束/延后/设置。"""
import os
import sys
import tempfile
import tkinter as tk

sys.path.insert(0, r"E:\software\work\water_break_reminder")
import water_break_reminder as W

# 用临时配置，避免污染真实 config.json
W.CONF_PATH = os.path.join(tempfile.gettempdir(), "wbr_smoke_test_config.json")
if os.path.exists(W.CONF_PATH):
    os.remove(W.CONF_PATH)

root = tk.Tk()
app = W.ReminderApp(root)
app.conf["sound"] = False          # 测试期间静音
root.update()
assert app.state == "running", app.state
assert app.remaining == 45 * 60, app.remaining
print("[ok] 初始状态 running, 倒计时 =", W.fmt(app.remaining))

app.conf["work_minutes"] = 1
app.remaining = 2
app.tick()          # -> 1
app.tick()          # -> 0 -> 触发休息
root.update()
assert app.state == "break", app.state
assert app.break_win is not None and app.break_win.winfo_exists()
print("[ok] 计时归零触发弹窗, state =", app.state, "休息倒计时 =", W.fmt(app.break_remaining))

# 休息倒计时走到 0 自动结束
app.break_remaining = 1
app.tick()
root.update()
assert app.state == "running", app.state
assert app.break_win is None
assert app.today_stats()["done"] == 1, app.today_stats()
print("[ok] 休息结束自动回到工作, 今日完成 =", app.today_stats()["done"])

# 手动弹窗 + 延后
app.start_break()
root.update()
assert app.state == "break"
app.delay_break(skip=False)        # 稍后提醒
root.update()
assert app.state == "running" and app.remaining == 5 * 60, app.remaining
print("[ok] 稍后提醒 ->", W.fmt(app.remaining))

# 手动弹窗 + 跳过
app.start_break()
root.update()
app.delay_break(skip=True)
root.update()
assert app.today_stats()["skip"] == 1
print("[ok] 跳过本次, 剩余 =", W.fmt(app.remaining), "跳过计数 =", app.today_stats()["skip"])

# 暂停/继续
app.toggle_pause(); assert app.state == "paused"
app.toggle_pause(); assert app.state == "running"
print("[ok] 暂停/继续")

# 休息暂停：暂停期间倒计时不动，恢复后继续走
app.start_break()
root.update()
assert app.state == "break" and app.break_paused is False
app.break_remaining = 60
app.set_break_paused(True)
assert app.state == "break", app.state
assert app.break_pause_btn.cget("text") == app.T("btn_resume")
assert app.pause_btn.cget("text") == app.T("btn_resume")
for _ in range(3):
    app.tick()
root.update()
assert app.break_remaining == 60, app.break_remaining
app.set_break_paused(False)
assert app.break_pause_btn.cget("text") == app.T("btn_pause")
app.tick()
root.update()
assert app.break_remaining == 59, app.break_remaining
print("[ok] 休息暂停/继续, 暂停 3 秒倒计时不动, 恢复后继续")

# 暂停状态下收尾：标志要复位，不能带进下一轮
app.set_break_paused(True)
app.finish_break(True)
root.update()
assert app.state == "running" and app.break_paused is False
print("[ok] 休息暂停后结束, 暂停标志已复位")

# 设置窗口
app.open_settings()
root.update()
assert app._set_win.winfo_exists()
app._set_win.destroy()
print("[ok] 设置窗口可打开")

# 进度条几何
app.conf["work_minutes"] = 45
app.remaining = 30 * 60
app.refresh_main()
coords = app.bar.coords(app.bar_fg)
assert len(coords) == 24 and coords[2] > 0, coords
print("[ok] 进度条几何正常, 前景宽度 = %.1f" % coords[2])

# 统计持久化
W.save_conf(app.conf)
reloaded = W.load_conf()
assert "stats" in reloaded and isinstance(reloaded["stats"], dict)
print("[ok] 配置读写正常, 文件 =", W.CONF_PATH)

# 开机自启：开 -> 校验 -> 关 -> 校验，最后恢复测试前的状态
orig = W.autostart_status()[0]
ok, msg = W.set_autostart(True)
assert ok, msg
st, cmd = W.autostart_status()
assert st == "on", (st, cmd)
assert W.SCRIPT_PATH.lower() in cmd.lower().replace('"', " "), cmd
assert "pythonw" in cmd.lower(), cmd
print("[ok] 开机自启开启 ->", cmd)

ok, msg = W.set_autostart(False)
assert ok, msg
assert W.autostart_status()[0] == "off", W.autostart_status()
print("[ok] 开机自启关闭，注册表项已清除")

ok, _ = W.set_autostart(False)          # 重复关闭应幂等
assert ok, "重复关闭应当成功"
print("[ok] 重复关闭幂等")

if orig == "on":
    W.set_autostart(True)
    print("[ok] 已恢复测试前状态：开启")

app.stop_ring()
root.destroy()
os.remove(W.CONF_PATH)
print("\n全部通过 ✔")
