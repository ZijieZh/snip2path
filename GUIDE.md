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

双击桌面上的 **Snip2Path** 快捷方式，弹出一个命令行窗口，显示"Snip2Path daemon started"就表示在运行了。

### 粘贴图片到终端

1. `Win+Shift+S` 截图
2. 切回终端（Claude Code / Cursor / 命令行）
3. `Ctrl+V` — 粘贴出图片文件路径
4. 回车发送

### 粘贴图片到微信/钉钉

直接 `Ctrl+V`，跟平时一样，图片正常粘贴。

### 关闭

关掉那个命令行窗口就行。

---

## 修改代码后上传

当你改了代码、修了 bug、加了功能后，按这三步上传：

### 第 1 步：进入项目文件夹

打开终端（Git Bash），输入：

```bash
cd C:/AI/snip2path
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
cd C:/AI/snip2path
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

## v1.1 新功能：智能前台检测

监听模式现在会自动检测当前窗口类型：

| 当前窗口 | 截图后 Ctrl+V 效果 |
|----------|-------------------|
| 终端（cmd/PowerShell/Git Bash/Code/Cursor） | 粘贴路径 |
| 浏览器（Kimi/ChatGPT/豆包等） | 仅粘贴图片 |
| 微信 / 钉钉 | 仅粘贴图片 |

如果自动检测不准，可以手动指定：
- `snip2path --watch --always-text` — 始终附带路径
- `snip2path --watch --no-text` — 始终不动剪贴板

---

## 常用命令速查

| 命令 | 作用 |
|------|------|
| `snip2path` | 一次性保存当前剪贴板图片 |
| `snip2path --watch` | 启动监听模式 |
| `snip2path -o D:\图片` | 改输出目录 |
| `snip2path -p ss_` | 改文件名前缀 |
| `snip2path --always-text` | 强制附带路径（不分场景） |
| `snip2path --no-text` | 强制不修改剪贴板（只保存文件） |
| `snip2path -v` | 查看版本 |
| `snip2path -h` | 查看帮助 |
| `git status` | 查看哪些文件改过了 |
| `git diff` | 查看具体改了什么 |
| `git log --oneline` | 查看提交历史 |

---

## 项目结构

```
snip2path/
├── snip2path.py          ← 核心代码，这是你要改的文件
├── pyproject.toml        ← 项目配置（版本号、依赖等）
├── README.md             ← 英文说明
├── README_CN.md          ← 中文说明
├── LICENSE               ← MIT 协议
├── scripts/
│   ├── install.bat       ← 一键安装脚本
│   └── start.bat         ← 启动监听脚本
└── tests/
    └── test_snip2path.py ← 测试代码，改完核心代码后跑一下
```

**改完代码后跑测试**：
```bash
cd C:/AI/snip2path
python tests/test_snip2path.py
```
11 个测试全部 `ok` 才算通过。

---

## 更新版本号

改了功能后记得更新版本号，有两处要改：

1. **pyproject.toml**：`version = "1.0.0"` → `version = "1.0.1"`
2. **snip2path.py**：`VERSION = "1.0.0"` → `VERSION = "1.0.1"`
