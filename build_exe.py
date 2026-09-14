# -*- coding: utf-8 -*-
"""
一键打包成单文件 exe（PyInstaller）。

用法：
    python build_exe.py

产物：
    dist/SitReminder.exe

说明：
    - 打包后配置写在 exe 同目录的 config.json
    - app.ico 会被一起打进去
    - 若没装 PyInstaller，脚本会提示安装命令
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(HERE, "water_break_reminder.py")
ICON = os.path.join(HERE, "app.ico")
NAME = "SitReminder"


def main():
    if not os.path.exists(MAIN):
        sys.exit("找不到主程序：%s" % MAIN)

    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        sys.exit(
            "还没装 PyInstaller。请先运行：\n"
            "    %s -m pip install pyinstaller" % sys.executable
        )

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

    print("执行：%s" % " ".join(cmd))
    r = subprocess.call(cmd, cwd=HERE)
    if r != 0:
        sys.exit("打包失败，退出码 %d" % r)

    exe = os.path.join(HERE, "dist", NAME + ".exe")
    if os.path.exists(exe):
        print("\n✅ 打包完成：%s  (%.1f MB)" % (exe, os.path.getsize(exe) / 1048576.0))
        print("   把这个 exe 单独拷走就能用，不需要 Python。")
    else:
        sys.exit("没有找到产物，请检查上面的日志。")


if __name__ == "__main__":
    main()
