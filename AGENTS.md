# AGENTS.md

给 AI 编码助手的项目说明。人类请先读 [README.md](README.md)。

## 项目一句话

Windows 桌面久坐提醒工具。纯 Python 标准库（`tkinter`）实现，**零第三方依赖**，支持中/英/日/韩四语言。打包为单文件 exe 分发。

## 快速命令

```bash
# 运行（GUI 程序，不会自动退出）
pythonw water_break_reminder.py            # 推荐，无控制台
python water_break_reminder.py             # 带控制台，便于看报错
python water_break_reminder.py --lang=en   # 强制指定语言
python water_break_reminder.py --selftest  # 构建全部界面后立即退出，用于验证

# 验证（改完代码务必都跑一遍）
python _smoke_test.py                      # 15 项功能冒烟测试
python tools/verify_layout.py              # 416 组合排版校验（4 语言 × 13 动作 × 4 顺便 × 2 态）
python tools/autostart.py verify           # 真跑一次开机自启命令

# 打包
python build_exe.py                        # 缺 PyInstaller 会自动装
python build_exe.py --no-install           # CI 用：缺了直接报错，不偷偷装

# 截图（生成 screenshots/ 下的四语言界面图）
python tools/capture_ui.py                 # 全部语言
python tools/capture_ui.py --lang=en       # 单个语言
```

## 架构

```
water_break_reminder.py   # 主程序：窗口、计时状态机、注册表自启
i18n.py                   # 四语言文案 + 字体候选链 + 系统语言探测
build_exe.py              # 生成 .spec 后调 PyInstaller
tools/                    # 开发期辅助脚本（不参与打包）
  autostart.py            #   自启的命令行管理：status / on / off / verify
  capture_ui.py           #   无遮挡窗口截图（Win32 PrintWindow）
  verify_layout.py        #   穷举 416 种文案/状态组合，检测内容溢出
  dpi_probe.py            #   三种 DPI 模式对比诊断
  make_icon.py            #   生成 app.ico
_smoke_test.py            # 功能冒烟测试
```

### 计时状态机

```
running ──(计时归零)──> break ──(倒计时结束 / 我已完成休息)──> running
```

`state` 只有三个取值：`running` / `paused` / `break`。

**休息暂停**不用第四个状态，而是 `state == "break"` + 布尔量 `break_paused`：

```python
bp = (self.state == "break" and self.break_paused)
```

这样所有 `if self.state == "break"` 的判断（弹窗是否开着、能不能重置等）都不用改。
`tick()` 里 `if not self.break_paused:` 才走倒计时。新增涉及「休息中」的逻辑时，
记得同时考虑 `break_paused`——配色、提示语、按钮文案都要分两态。

旁路操作：

- `pause` / `resume` —— 停在当前进度，不重置
- `snooze` —— 从 `break` 回到 `running`，剩余时间 = `snooze_minutes`
- `skip` —— 跳过本次，剩余时间 = 1 分钟
- `break_now` —— 立即进入 `break`

状态文案由 `st_running` / `st_break` / `st_paused` 三个键控制；休息暂停时弹窗标题用
`break_paused`，主窗口复用 `paused_hint`。

**暂停/继续只有一个入口**：`toggle_pause()`，它按当前 state 分派。主窗口按钮、
休息弹窗按钮、空格键都调它，保证行为一致。

**离开 break 必须复位 `break_paused`**：`finish_break()` 和 `delay_break()` 里都有
`self.break_paused = False`，新增任何退出休息的路径时别忘了这一点，否则暂停状态会
带到下一轮计时。

## 必须遵守的约定

### 1. 面向用户的文字一律走 i18n，不要硬编码

```python
# 错
tk.Label(w, text="设置")

# 对
tk.Label(w, text=self.T("set_title"))
```

新增文案时 **四个语言的 key 必须同时补齐**。`tools/verify_layout.py` 会穷举所有语言 × 动作组合，漏翻译会在 CI 之外的本地校验里直接暴露。

`i18n.UI` 的结构是 `{lang: {key: text}}`，占位符用 `{n}` / `{t}` / `{name}` 等，通过 `text(lang, key, **kw)` 格式化。

### 2. 所有像素尺寸过 `self.P()`

```python
# 错 —— 150% 缩放下会大面积折行
padx=20

# 对
padx=self.P(20)
```

原因：`tkinter` 的字体单位是「点」，会随系统缩放自动放大，但像素尺寸不会。`P(n) = round(n * k)`，`k` 由 `tk scaling` 推导。**字号不用过 P()**，Tk 自己会处理。

### 3. 窗口尺寸不要写死

先 `withdraw()` → 建控件 → `update_idletasks()` → 量 `winfo_reqheight()` → `geometry()` → `deiconify()`。直接设固定高度会因语言/字体不同而裁切。

**注意**：`withdraw` 状态下 `winfo_reqheight()` 会虚高，必须在 `update_idletasks()` 之后取值。

### 4. 不要给主程序加第三方依赖

这是本项目的核心卖点（README 第一句就是「零第三方依赖」）。`build_exe.py` 用到的 PyInstaller 只是**打包期**依赖，不进运行时。

### 5. 脚本里的中文输出必须防 cp1252

CI runner 是英文 Windows，`sys.stdout.encoding` 是 cp1252，直接 `print` 中文会抛 `UnicodeEncodeError` 让脚本崩掉。任何会被 CI 调用、且含非 ASCII 输出的脚本，开头都要加：

```python
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
```

本地验证（中文系统下这个 bug 永远暴露不出来）：

```bash
PYTHONIOENCODING=cp1252 python build_exe.py --no-install
```

## 容易踩的坑

### Tk 相关

- **测试时不要共用同一个 `tk.Tk()` 根**。多个 `ReminderApp` 堆在一个 root 上会让 `winfo_reqheight()` 累加出假高度（曾量到 1410px，实际只有 437px）。每个语言/场景建独立 `Tk()` 并销毁。
- **GUI 需要带 tkinter 的 Python**。部分精简发行版（含 WorkBuddy 托管的 Python）没有 tkinter，`import tkinter` 直接失败。
- **截当前窗口要用 `PrintWindow(hwnd, memDC, 2)`**（`PW_RENDERFULLCONTENT`）+ `GetDIBits`。且必须显式声明 ctypes `argtypes`，否则 64 位句柄会溢出报 `OverflowError`。
- **给 Toplevel 绑快捷键要防按钮抢键**。点击 Tk 按钮会让它获得焦点，此时按 `空格`
  会先被 Button 的类绑定消费掉一次，再冒泡到 Toplevel 绑定，**同一次按键触发两遍**
  （连按两下 = 没按）。所以绑的处理器要判 `event.widget`：

  ```python
  def _key_pause(self, event):
      if isinstance(event.widget, tk.Button):   # 按钮已处理，别重复触发
          return
      self.toggle_pause()
  ```

### 打包相关

- **不要用命令行 `--add-data`**。`;`（Windows 分隔符）在 cmd / PowerShell / bash 下解析行为不同，CI 上必踩。项目改为 `build_exe.py` 生成 `.spec` 文件，datas / icon 走 Python 字面量，不经过 shell。
- **`.spec` / `build/` / `dist/` 已进 `.gitignore`**，不要提交。
- 打包后 `config.json` 写在 **exe 同目录**（不是临时解包目录），资源用 `sys._MEIPASS`。见主程序顶部的 `FROZEN` / `APP_DIR` / `RES_DIR`。

### 测试相关

- **测试绝不许污染真实的 `config.json`**。用户实机配置（窗口位置、自启状态、统计）不能被测试覆盖。测试脚本要把 `W.CONF_PATH` 指向临时文件，结束后还原自启状态。参考 `_smoke_test.py` 的做法。

### 环境相关

- **Bash 的 PATH 可能损坏**（`dirname` / `ls` / `grep` 全部 not found），且 bash 里多行 `python -c` 的引号容易被 shell shim 撕碎。稳妥做法：把脚本写成 `.py` 文件再执行，不要在命令行里塞长 Python 代码。
- **往文件写含反引号的文本，不要走 `python -c "..."`**，反引号会被 shell 当命令替换执行掉。先写临时文件再读取追加。
- **`git push` 时显式写分支名**（`git push origin main`）。部分环境下 `refs/remotes/` 嵌套引用无法落盘，`git status` 会持续显示 `[gone]`，但 push/pull 正常，忽略即可。

## CI

`.github/workflows/release.yml`：推送 `v*` tag 时自动在 `windows-latest` 上构建 exe，挂到 GitHub Release。

```bash
git tag -a v1.0.1 -m "..." && git push origin v1.0.1
```

排查 CI 失败的提示：

- 未认证时 `actions/jobs/<id>/logs` 返回 **403**、artifact 下载 **401**、失败 job 的 `check-runs` output 常为空
- 可用 `check-runs/<job_id>/annotations`（免认证，但只给到行号和退出码）
- 需要完整 traceback 时，让 workflow 在 `if: failure()` 里把报告推到临时孤儿分支，再用 `git fetch origin <branch>` 读取
- GitHub API 无认证限 **60 次/小时**，轮询会很快耗尽。省流替代：`git ls-remote origin <ref>` 判引用、读 `<repo>/releases.atom` 判 Release

## 改动完成后

1. `python _smoke_test.py` —— 功能没坏
2. `python tools/verify_layout.py` —— 没有文案溢出
3. 改动了界面文案或排版 → `python tools/capture_ui.py` 更新截图（每语言 4 张：
   主窗 / 休息 / 休息暂停 / 设置）
4. 改动了 CI 或构建脚本 → 用上面的 `PYTHONIOENCODING=cp1252` 先本地过一遍
