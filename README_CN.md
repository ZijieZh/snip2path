# Snip2Path

<p align="center">
  <img src="assets/header.png" alt="Snip2Path" width="100%">
</p>

**截图后 Ctrl+V：终端粘贴路径，微信/钉钉粘贴图片。**

[English](README.md) | [MIT License](LICENSE)

## 解决的问题

截图后想在终端工具（Claude Code、Cursor 等）里粘贴图片？终端不支持图片粘贴。你得先保存文件、找到路径、拖进来、或者手动输入路径。

## 解决方案

Snip2Path 后台监听剪贴板。当你截图后：

1. 自动保存图片到 `~/Pictures/Snip2Path/`
2. 在剪贴板中同时保留**文件路径**（文本）+ **原始位图**（图片）

不同程序各取所需：

| 程序 | 读取的格式 | 粘贴结果 |
|------|-----------|----------|
| 终端 / 命令行 | `CF_UNICODETEXT` | `C:\Users\...\Pictures\Snip2Path\snip_143025.png` |
| 微信 / 钉钉 | `CF_DIB` | 图片本身 |

## 快速开始

### 安装

```bash
pip install snip2path
```

安装方式：
- **Windows**：双击 `scripts/install.bat`
- **macOS**：运行 `bash scripts/install-macos.sh`
- **Linux**：运行 `bash scripts/install-linux.sh`

### 使用

```bash
# 监听模式（推荐）—— 后台运行，自动处理截图
snip2path --watch

# 一次性模式 —— 处理当前剪贴板图片
snip2path
```

### 工作流

**Windows：**
1. 启动 `snip2path --watch`（窗口保持打开）
2. 截图（`Win+Shift+S`）
3. 切到终端 → `Ctrl+V` → 粘贴出文件路径
4. 切到微信 → `Ctrl+V` → 粘贴出图片

**macOS：**
1. 启动 `snip2path --watch`（或 `nohup snip2path --watch --silent &`）
2. 截图（`Cmd+Ctrl+Shift+4`）
3. 切到终端 → `Cmd+V` → 粘贴出文件路径
4. 切到微信 → `Cmd+V` → 粘贴出图片

**Linux：**
1. 启动 `snip2path --watch`（或 `nohup snip2path --watch --silent &`）
2. 截图（取决于桌面环境，如 `gnome-screenshot` 或 `flameshot`）
3. 切到终端 → `Ctrl+V` → 粘贴出文件路径
4. 切到聊天软件 → `Ctrl+V` → 粘贴出图片

## 系统要求

- **Windows**：Python 3.8+，Pillow ≥ 9.0
- **macOS**：Python 3.8+，Pillow ≥ 9.0，pyobjc-framework-Cocoa ≥ 10.0
- **Linux**：Python 3.8+，Pillow ≥ 9.0，xclip（X11）或 wl-clipboard（Wayland）

## 命令行参数

```
snip2path                 一次性处理当前剪贴板图片
snip2path --watch         监听模式：持续监控剪贴板
snip2path -o ~/screenshots 自定义输出目录
snip2path -p ss_          自定义文件名前缀
snip2path -v              显示版本号
snip2path -h              显示帮助
```

## 平台差异

**Linux 限制：** Linux 剪贴板（X11 / Wayland）无法同时保存图片和文本。Snip2Path 默认将图片恢复到剪贴板，聊天软件可粘贴图片。若需要在终端粘贴文件路径，使用 `snip2path --with-text`（仅路径）或 `snip2path --no-clipboard`（仅保存，不修改剪贴板）。

## 原理

Windows 剪贴板支持多种数据格式共存。Snip2Path 的工作流程：

1. 检测剪贴板变化（`GetClipboardSequenceNumber`）
2. 读取原始位图数据（`CF_DIB`、`CF_DIBV5`、`CF_BITMAP`）
3. 保存 PNG 副本到磁盘
4. 重新写入剪贴板：**同时包含**原始位图格式 + 文本路径格式（`CF_UNICODETEXT`）

这样，每个程序选择自己偏好的格式读取。终端程序读文本路径，支持图片的程序读位图数据。

## 参与贡献

欢迎提 Issue 和 PR。

```bash
git clone https://github.com/ZijieZh/snip2path.git
cd snip2path
pip install -e .
python tests/test_snip2path.py
```

## 许可证

MIT — 详见 [LICENSE](LICENSE)。
