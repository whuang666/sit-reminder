# -*- coding: utf-8 -*-
"""
一键打包成单文件 exe（PyInstaller）。

用法：
    python build_exe.py              # 缺 PyInstaller 会自动装
    python build_exe.py --no-install # 不自动安装，缺了直接报错

产物：
    dist/SitReminder.exe

说明：
    - 打包后配置写在 exe 同目录的 config.json
    - app.ico 会被一起打进去
    - PyInstaller 直接以模块方式调用，不再依赖 PATH 里的 `pyinstaller` 命令，
      所以换任何 Python 解释器跑都能得到一致行为（CI 上尤其重要）
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(HERE, "water_break_reminder.py")
ICON = os.path.join(HERE, "app.ico")
NAME = "SitReminder"


def log(msg):
    print(msg, flush=True)


def have_pyinstaller():
    try:
        import PyInstaller  # noqa: F401
        return True
    except ImportError:
        return False


def ensure_pyinstaller(auto_install=True):
    if have_pyinstaller():
        return
    if not auto_install:
        sys.exit(
            "还没装 PyInstaller。请先运行：\n"
            "    %s -m pip install pyinstaller" % sys.executable
        )
    log("未检测到 PyInstaller，正在为当前解释器安装……")
    log("    %s" % sys.executable)
    r = subprocess.call([sys.executable, "-m", "pip", "install",
                         "--upgrade", "pyinstaller"])
    if r != 0:
        log("pip 安装失败，尝试加 --user 重试……")
        r = subprocess.call([sys.executable, "-m", "pip", "install",
                             "--user", "--upgrade", "pyinstaller"])
    if r != 0:
        sys.exit("PyInstaller 安装失败（退出码 %d）" % r)
    # 安装后重新确认（必须换新进程才看得到？同进程 import 也行，但稳妥起见核对一次）
    if not have_pyinstaller():
        r = subprocess.call([sys.executable, "-c", "import PyInstaller"])
        if r != 0:
            sys.exit("PyInstaller 装好了但导不进来，请检查环境。")
    log("PyInstaller 就绪。")


def main():
    auto = "--no-install" not in sys.argv

    if not os.path.exists(MAIN):
        sys.exit("找不到主程序：%s" % MAIN)

    # tkinter 是硬依赖，缺了打包出来也是坏的，先挡住
    r = subprocess.call([sys.executable, "-c", "import tkinter"])
    if r != 0:
        sys.exit(
            "当前解释器缺少 tkinter，无法打包：\n"
            "    %s\n"
            "Windows 官方安装包请勾选 tcl/tk；conda 环境一般自带。" % sys.executable
        )

    ensure_pyinstaller(auto)

    # 清理旧产物
    for d in ("build", "dist"):
        p = os.path.join(HERE, d)
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",            # 单文件
        "--windowed",           # 不弹控制台
        "--name", NAME,
        "--distpath", os.path.join(HERE, "dist"),
        "--workpath", os.path.join(HERE, "build"),
        "--specpath", HERE,
    ]
    if os.path.exists(ICON):
        cmd += ["--icon", ICON]
        cmd += ["--add-data", "%s%s." % (ICON, os.pathsep)]

    cmd.append(MAIN)

    log("执行：%s" % " ".join(cmd))
    r = subprocess.call(cmd, cwd=HERE)
    if r != 0:
        sys.exit("打包失败，退出码 %d" % r)

    exe = os.path.join(HERE, "dist", NAME + ".exe")
    if os.path.exists(exe):
        log("\n✅ 打包完成：%s  (%.1f MB)" % (exe, os.path.getsize(exe) / 1048576.0))
        log("   把这个 exe 单独拷走就能用，不需要 Python。")
    else:
        sys.exit("没有找到产物，请检查上面的日志。")


if __name__ == "__main__":
    main()
