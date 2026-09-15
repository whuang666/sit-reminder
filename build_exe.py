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
    - 不直接拼命令行，而是先写 .spec 文件再交给 PyInstaller 跑。
      这样彻底避开 --add-data 里 `;` / `:` 在不同 shell（cmd / PowerShell / bash）
      下被当成命令分隔符的问题，CI 上尤其容易踩。
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(HERE, "water_break_reminder.py")
ICON = os.path.join(HERE, "app.ico")
NAME = "SitReminder"
SPEC = os.path.join(HERE, NAME + ".spec")

# CI（英文版 Windows）的 stdout 默认是 cp1252，直接 print 中文会抛
# UnicodeEncodeError 把脚本打死。这里强制切到 UTF-8，切不动就退回
# 「无法编码的字符替换掉」，保证任何环境下都不会因为日志而失败。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def log(msg):
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "ascii"
        print(msg.encode(enc, "replace").decode(enc, "replace"), flush=True)



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
    for extra in ([], ["--user"]):
        r = subprocess.call([sys.executable, "-m", "pip", "install"] + extra
                            + ["--upgrade", "pyinstaller"])
        if r == 0:
            break
    else:
        sys.exit("PyInstaller 安装失败")
    if not have_pyinstaller():
        r = subprocess.call([sys.executable, "-c", "import PyInstaller"])
        if r != 0:
            sys.exit("PyInstaller 装好了但导不进来，请检查环境。")
    log("PyInstaller 就绪。")


def write_spec():
    """手写 spec，避免命令行分隔符坑；同时也让构建可复现。"""
    datas = ""
    if os.path.exists(ICON):
        # add-data 里 src 用原始字符串，避免 Windows 反斜杠被当转义
        datas = "\n    datas=[(r'%s', '.')]," % ICON
    icon_arg = "icon=r'%s'," % ICON if os.path.exists(ICON) else ""

    spec = """# -*- mode: python ; coding: utf-8 -*-
# 由 build_exe.py 自动生成，可手工微调后直接 `pyinstaller SitReminder.spec`

a = Analysis(
    [r'%s'],%s
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='%s',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,          # GUI 程序，不弹黑窗
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    %s
)
""" % (MAIN, datas, NAME, icon_arg)

    with open(SPEC, "w", encoding="utf-8") as f:
        f.write(spec)
    log("已生成 %s" % SPEC)
    return SPEC


def main():
    auto = "--no-install" not in sys.argv

    if not os.path.exists(MAIN):
        sys.exit("找不到主程序：%s" % MAIN)

    # tkinter 是硬依赖，缺了包出来也是坏的
    if subprocess.call([sys.executable, "-c", "import tkinter"]) != 0:
        sys.exit(
            "当前解释器缺少 tkinter，无法打包：\n"
            "    %s\n"
            "Windows 官方安装包请勾选 tcl/tk；conda 环境一般自带。" % sys.executable
        )

    ensure_pyinstaller(auto)

    for d in ("build", "dist"):
        p = os.path.join(HERE, d)
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)

    spec = write_spec()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath", os.path.join(HERE, "dist"),
        "--workpath", os.path.join(HERE, "build"),
        spec,
    ]
    log("执行：%s" % " ".join(cmd))
    r = subprocess.call(cmd, cwd=HERE)
    if r != 0:
        # 把 warn 文件打出来，CI 上没日志权限时这是唯一线索
        warn = os.path.join(HERE, "build", NAME, "warn-%s.txt" % NAME)
        if os.path.exists(warn):
            log("\n---- PyInstaller 警告 ----")
            with open(warn, encoding="utf-8", errors="replace") as f:
                log(f.read()[:4000])
        sys.exit("打包失败，退出码 %d" % r)

    exe = os.path.join(HERE, "dist", NAME + ".exe")
    if os.path.exists(exe):
        log("\n✅ 打包完成：%s  (%.1f MB)" % (exe, os.path.getsize(exe) / 1048576.0))
        log("   把这个 exe 单独拷走就能用，不需要 Python。")
    else:
        sys.exit("没有找到产物，请检查上面的日志。")


if __name__ == "__main__":
    main()
