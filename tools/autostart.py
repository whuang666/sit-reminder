# -*- coding: utf-8 -*-
"""
开机自启开关（命令行版，供 .bat 或手动调用）。
用法：
    python tools/autostart.py            查看状态
    python tools/autostart.py on         开启
    python tools/autostart.py off        关闭
    python tools/autostart.py verify     真正跑一遍自启命令，确认开机时能起来
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import water_break_reminder as W  # noqa: E402


def show_status():
    st, cmd = W.autostart_status()
    label = {"on": "已开启", "off": "未开启", "stale": "已登记，但路径已失效"}[st]
    print("状态     ：%s" % label)
    print("启动器   ：%s" % W.autostart_exe())
    print("脚本     ：%s" % W.SCRIPT_PATH)
    print("注册表项 ：HKCU\\%s" % W.RUN_KEY)
    print("值名     ：%s" % W.RUN_NAME)
    print("已登记值 ：%s" % (cmd or "（无）"))


def verify():
    """按注册的那条命令真跑一次（--selftest 模式，构建界面后立即退出）"""
    st, cmd = W.autostart_status()
    if st == "off":
        print("当前未开启自启，没有可验证的命令。先执行 on。")
        return 1
    if st == "stale":
        print("注册的路径已失效，重新执行 on 修复。")
        return 1
    print("注册的命令：%s" % cmd)
    print("模拟开机执行中（构建界面后立即退出）...")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        r = subprocess.run([W.autostart_exe(), W.SCRIPT_PATH, "--selftest"],
                           capture_output=True, encoding="utf-8",
                           errors="replace", timeout=120, env=env)
    except Exception as e:
        print("执行失败：%s" % e)
        return 1
    out = (r.stdout or "").strip()
    err = (r.stderr or "").strip()
    if out:
        print(out)
    if err:
        print("stderr：%s" % err)
    ok = r.returncode == 0
    print("结论：%s（退出码 %s）"
          % ("开机自启可用 ✔" if ok else "开机自启不可用 ✘", r.returncode))
    return 0 if ok else 1


def main():
    arg = (sys.argv[1] if len(sys.argv) > 1 else "status").strip().lower()

    if arg in ("status", "s"):
        show_status()
        return 0
    if arg in ("on", "1", "enable", "true"):
        ok, msg = W.set_autostart(True)
        print(("开启成功：" if ok else "开启失败：") + msg)
        if ok:
            print()
            show_status()
        return 0 if ok else 1
    if arg in ("off", "0", "disable", "false"):
        ok, msg = W.set_autostart(False)
        print(("关闭成功：" if ok else "关闭失败：") + msg)
        return 0 if ok else 1
    if arg in ("verify", "v", "test"):
        return verify()

    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
