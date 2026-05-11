# Snip2Path 使用与维护指南

## 目录
- [日常使用](#日常使用)
- [修改代码后上传](#修改代码后上传)
- [从 GitHub 下载到新电脑](#从-github-下载到新电脑)
- [常用命令速查](#常用命令速查)
- [项目结构](#项目结构)

---

## 日常使用

### 启动监听

双击桌面上的 **Snip2Path Background** 快捷方式，程序在后台静默运行（无窗口弹出）。

### 粘贴图片到终端

1. `Win+Shift+S` 截图
2. 切回终端（Claude Code / Cursor / 命令行）
3. `Ctrl+V` — 粘贴出图片文件路径
4. 回车发送

### 粘贴图片到微信/钉钉

直接 `Ctrl+V`，跟平时一样，图片正常粘贴。

### 关闭

双击桌面上的 **Stop Snip2Path** 快捷方式即可关闭。

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

```bash
pip install Pillow setuptools
pip install -e .
```

安装完成后，终端输入 `snip2path --version` 验证。

---

## v1.2 核心机制

Snip2Path 使用 CF_HDROP（文件拖放列表）格式写入剪贴板：

| 粘贴位置 | 效果 | 原因 |
|----------|------|------|
| 终端（cmd/PowerShell/Git Bash/Code/Cursor） | 粘贴路径 | 终端读 CF_HDROP → 文件路径文本 |
| 浏览器（Kimi/ChatGPT/豆包等） | 仅图片 | 浏览器文本输入框忽略 CF_HDROP |
| 微信 / 钉钉 | 仅图片 | 读 CF_DIB 图片格式 |

如有特殊需求：
- `snip2path --watch --with-text` — 同时附带 CF_UNICODETEXT（老终端兼容）
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
│   ├── install.bat          ← 一键安装脚本
│   ├── start.bat            ← 启动监听脚本（最小化窗口）
│   ├── start-background.bat ← 启动监听脚本（无窗口后台）
│   └── stop.bat             ← 停止后台监听
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

1. **pyproject.toml**：`version = "1.0.0"` → `version = "1.0.1"`
2. **snip2path.py**：`VERSION = "1.0.0"` → `VERSION = "1.0.1"`
