# Snip2Path 使用与维护指南

## 目录
- [日常使用](#日常使用)
- [修改代码后上传](#修改代码后上传)
- [从 GitHub 下载到新电脑](#从-github-下载到新电脑)
- [常用命令速查](#常用命令速查)
- [项目结构](#项目结构)

---

## 日常使用

### Windows

**启动监听：** 双击桌面上的 **Snip2Path Background** 快捷方式，程序在后台静默运行（无窗口弹出）。

**截图：** `Win+Shift+S`

**粘贴：**
- 终端 → `Ctrl+V` → 文件路径
- 微信/钉钉 → `Ctrl+V` → 图片

**关闭：** 双击桌面上的 **Stop Snip2Path** 快捷方式。

### macOS

**启动监听：**
```bash
snip2path --watch
```
或后台运行：
```bash
nohup snip2path --watch --silent > /dev/null 2>&1 &
```

**截图：** `Cmd+Ctrl+Shift+4`（截图到剪贴板）

**粘贴：**
- 终端（iTerm2/Terminal.app） → `Cmd+V` → 文件路径
- 微信/钉钉 → `Cmd+V` → 图片

**关闭：**
```bash
pkill -f "snip2path --watch"
```

---

## 修改代码后上传

当你改了代码、修了 bug、加了功能后，按这三步上传：

### 第 1 步：进入项目文件夹

打开终端（Git Bash），输入：

```bash
cd C:/AI/exes/snip2path
```

### 第 2 步：提交修改

```bash
git add .
git commit -m "写清楚你改了什么，比如：修复了xxx问题"
```

### 第 3 步：推送到 GitHub

```bash
git push
```

完成后刷新 https://github.com/ZijieZh/snip2path 就能看到更新了。

### 完整示例

```bash
cd C:/AI/exes/snip2path
git add .
git commit -m "v1.0.1: 增加自定义文件名后缀功能"
git push
```

---

## 从 GitHub 下载到新电脑

### 1. 安装 Python

去 https://www.python.org/downloads/ 下载安装，勾选"Add Python to PATH"。

### 2. 安装 Git

去 https://git-scm.com/download/win 下载安装。

### 3. 生成 SSH 密钥并添加到 GitHub

打开终端（Git Bash），依次运行：

```bash
# 生成密钥（把邮箱换成你的）
ssh-keygen -t ed25519 -C "你的邮箱" -f "$HOME/.ssh/id_ed25519" -N ""

# 显示公钥，复制整行
cat "$HOME/.ssh/id_ed25519.pub"
```

然后浏览器打开 https://github.com/settings/ssh/new ，粘贴公钥，保存。

### 4. 下载项目

```bash
cd C:/AI
git clone git@github.com:ZijieZh/snip2path.git
cd snip2path
```

### 5. 安装依赖和项目

**Windows：**
```bash
pip install Pillow setuptools
pip install -e .
```

**macOS：**
```bash
pip3 install Pillow "pyobjc-framework-Cocoa>=10.0"
pip3 install -e .
```

安装完成后，终端输入 `snip2path --version` 验证。

---

## v1.3 核心机制

### Windows

使用 Win32 多格式剪贴板（CF_DIB + CF_HDROP）：

| 粘贴位置 | 效果 | 原因 |
|----------|------|------|
| 终端（cmd/PowerShell/Git Bash） | 粘贴路径 | 终端读 CF_HDROP → 文件路径文本 |
| 浏览器（Kimi/ChatGPT） | 仅图片 | 浏览器文本输入框忽略 CF_HDROP |
| 微信 / 钉钉 | 仅图片 | 读 CF_DIB 图片格式 |

### macOS

使用 NSPasteboard 多格式（public.png + public.utf8-plain-text）：

| 粘贴位置 | 效果 | 原因 |
|----------|------|------|
| 终端（iTerm2/Terminal.app/Warp） | 粘贴路径 | 终端读 public.utf8-plain-text |
| 浏览器（Kimi/ChatGPT） | 粘贴路径 | 无 CF_HDROP 等价物（已知限制） |
| 微信 / 钉钉 | 仅图片 | 读 public.png 图片格式 |

如有特殊需求：
- `snip2path --watch --with-text` — 同时附带文本路径（老终端兼容）
- `snip2path --watch --no-clipboard` — 只保存不修改剪贴板

---

## 常用命令速查

| 命令 | 作用 |
|------|------|
| `snip2path` | 一次性保存当前剪贴板图片 |
| `snip2path --watch` | 启动监听模式 |
| `snip2path -o D:\图片` | 改输出目录 |
| `snip2path -p ss_` | 改文件名前缀 |
| `snip2path --with-text` | 同时附带文本路径（老终端兼容） |
| `snip2path --no-clipboard` | 只保存不修改剪贴板 |
| `snip2path -v` | 查看版本 |
| `snip2path -h` | 查看帮助 |

| 桌面快捷方式 | 作用 |
|------|------|
| **Snip2Path Background** | 启动后台监听（无窗口） |
| **Stop Snip2Path** | 停止后台监听 |

---

## 项目结构

```
snip2path/
├── snip2path.py          ← 核心代码，这是你要改的文件
├── pyproject.toml        ← 项目配置（版本号、依赖等）
├── README.md             ← 英文说明
├── README_CN.md          ← 中文说明
├── GUIDE.md              ← 使用与维护指南（本文档）
├── LICENSE               ← MIT 协议
├── assets/
│   └── header.png        ← 宣传海报
├── scripts/
│   ├── install.bat          ← Windows 一键安装
│   ├── start.bat            ← Windows 启动（最小化窗口）
│   ├── start-background.bat ← Windows 启动（无窗口后台）
│   ├── stop.bat             ← Windows 停止
│   ├── install-macos.sh     ← macOS 安装
│   ├── start-macos.sh       ← macOS 启动（后台）
│   └── stop-macos.sh        ← macOS 停止
└── tests/
    └── test_snip2path.py    ← 测试代码（21个用例）
```

**改完代码后跑测试**：
```bash
cd C:/AI/exes/snip2path
python tests/test_snip2path.py
```
21 个测试全部 `ok` 才算通过。

---

## 更新版本号

改了功能后记得更新版本号，有两处要改：

1. **pyproject.toml**：`version = "1.3.0"` → `version = "1.3.1"`
2. **snip2path.py**：`VERSION = "1.3.0"` → `VERSION = "1.3.1"`
