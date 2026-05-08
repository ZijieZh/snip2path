# -*- coding: utf-8 -*-
"""Snip2Path — Screenshot to clipboard path bridge for Windows

After screenshot (Win+Shift+S):
  Ctrl+V in terminal/cmd  → pastes image file path
  Ctrl+V in WeChat/DingTalk → pastes the image itself

How: Windows clipboard supports multiple formats simultaneously.
  - CF_DIB / CF_DIBV5 / CF_BITMAP → image (WeChat, DingTalk, etc.)
  - CF_UNICODETEXT               → file path (terminal, text editors)

Usage:
  snip2path           # once: save current clipboard image + set multi-format
  snip2path --watch   # daemon: monitor clipboard, auto-process new images
  snip2path -o ~/Pictures/Screenshots  # custom output directory
  snip2path -p ss_    # custom filename prefix
"""
import sys
import os
import hashlib
import ctypes
import time
import argparse
from io import BytesIO
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageGrab

VERSION = "1.1.1"
DEFAULT_OUTPUT = Path.home() / "Pictures" / "Snip2Path"
DEFAULT_PREFIX = "snip_"

# ── Terminal process names (foreground window detection) ──────────────────
TERMINAL_PROCS = {
    # Windows built-in
    "cmd.exe", "powershell.exe", "pwsh.exe",
    # Terminal emulators
    "windowsterminal.exe", "bash.exe", "sh.exe",
    "wsl.exe", "mintty.exe", "wezterm.exe",
    "alacritty.exe", "conemu.exe", "tabby.exe",
    "hyper.exe", "terminus.exe",
    # IDE terminals
    "code.exe", "cursor.exe", "windsurf.exe",
    "claude.exe",
}

# ── Windows API ──────────────────────────────────────────────────────────
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
gdi32 = ctypes.windll.gdi32
psapi = ctypes.windll.psapi

# 64-bit Windows: restype/argtypes required to prevent pointer truncation
kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = ctypes.c_void_p
kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
kernel32.GlobalUnlock.restype = ctypes.c_bool
kernel32.GlobalSize.argtypes = [ctypes.c_void_p]
kernel32.GlobalSize.restype = ctypes.c_size_t

user32.OpenClipboard.argtypes = [ctypes.c_void_p]
user32.OpenClipboard.restype = ctypes.c_bool
user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype = ctypes.c_bool
user32.EmptyClipboard.argtypes = []
user32.EmptyClipboard.restype = ctypes.c_bool
user32.GetClipboardData.argtypes = [ctypes.c_uint]
user32.GetClipboardData.restype = ctypes.c_void_p
user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
user32.SetClipboardData.restype = ctypes.c_void_p
user32.IsClipboardFormatAvailable.argtypes = [ctypes.c_uint]
user32.IsClipboardFormatAvailable.restype = ctypes.c_bool
user32.GetClipboardSequenceNumber.argtypes = []
user32.GetClipboardSequenceNumber.restype = ctypes.c_uint32
user32.CopyImage.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
user32.CopyImage.restype = ctypes.c_void_p

# Foreground window detection
user32.GetForegroundWindow.restype = ctypes.c_void_p
user32.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
user32.GetWindowThreadProcessId.restype = ctypes.c_uint32
kernel32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_bool, ctypes.c_uint32]
kernel32.OpenProcess.restype = ctypes.c_void_p
kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
kernel32.CloseHandle.restype = ctypes.c_bool
psapi.GetModuleBaseNameW.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32]
psapi.GetModuleBaseNameW.restype = ctypes.c_uint32

CF_BITMAP = 2
CF_DIB = 8
CF_UNICODETEXT = 13
CF_DIBV5 = 17

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"}

# ── Global state (set by CLI args) ───────────────────────────────────────
_output_dir = DEFAULT_OUTPUT
_prefix = DEFAULT_PREFIX
_always_text = False
_no_text = False


def get_foreground_process_name() -> str:
    """Return lowercase process name of the foreground window, or empty string."""
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""
    pid = ctypes.c_uint32()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return ""
    # PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
    h_proc = kernel32.OpenProcess(0x0400 | 0x0010, False, pid.value)
    if not h_proc:
        return ""
    buf = ctypes.create_unicode_buffer(260)
    psapi.GetModuleBaseNameW(h_proc, None, buf, 260)
    kernel32.CloseHandle(h_proc)
    return buf.value.lower()


def should_add_text() -> bool:
    """Decide whether to append text path to clipboard based on foreground window."""
    if _always_text:
        return True
    if _no_text:
        return False
    proc = get_foreground_process_name()
    return proc in TERMINAL_PROCS


def get_clipboard_seq() -> int:
    return user32.GetClipboardSequenceNumber()


# ── Single-instance guard ────────────────────────────────────────────────
_mutex_handle = None

def acquire_instance_lock() -> bool:
    """Try to acquire named mutex. Returns True if acquired, False if already running."""
    global _mutex_handle
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.GetLastError.restype = ctypes.c_uint32
    ERROR_ALREADY_EXISTS = 183

    h = kernel32.CreateMutexW(None, False, "Global\\Snip2Path_Watch_Mutex")
    _mutex_handle = h
    return not (h and kernel32.GetLastError() == ERROR_ALREADY_EXISTS)


# ── Clipboard read ───────────────────────────────────────────────────────
def get_clipboard_image():
    """Return (PIL.Image, fmt), (Path, fmt), or None if no image on clipboard."""
    try:
        img = ImageGrab.grabclipboard()
    except Exception:
        return None
    if img is None:
        return None
    # File path list (e.g., copied from File Explorer)
    if isinstance(img, list):
        for f in img:
            p = Path(str(f))
            if p.suffix.lower() in IMAGE_EXTS:
                return p, p.suffix[1:]
        return None
    # Bitmap object (screenshot, browser image copy, etc.)
    if hasattr(img, "save"):
        return img, "png"
    return None


def capture_raw_formats():
    """Capture raw bitmap formats from clipboard before modification.

    Returns {format_id: data_or_handle} for later restoration.
    Must be called AFTER get_clipboard_image(), BEFORE clipboard modification.
    """
    raw = {}
    user32.OpenClipboard(0)

    for cf in (CF_DIB, CF_DIBV5):
        if user32.IsClipboardFormatAvailable(cf):
            h = user32.GetClipboardData(cf)
            if h:
                size = kernel32.GlobalSize(h)
                if size > 0:
                    p = kernel32.GlobalLock(h)
                    data = ctypes.string_at(p, size)
                    kernel32.GlobalUnlock(h)
                    raw[cf] = data

    if user32.IsClipboardFormatAvailable(CF_BITMAP):
        h_bmp = user32.GetClipboardData(CF_BITMAP)
        if h_bmp:
            copy = user32.CopyImage(h_bmp, 0, 0, 0, 0)
            if copy:
                raw[CF_BITMAP] = copy

    user32.CloseClipboard()
    return raw


# ── Clipboard multi-format write ─────────────────────────────────────────
def set_clipboard_multiformat(raw_formats: dict, text: str):
    """Write bitmap formats + text path to clipboard.

    Terminal reads CF_UNICODETEXT → path.
    WeChat/DingTalk reads CF_DIB/CF_BITMAP → image.
    """
    user32.OpenClipboard(0)
    user32.EmptyClipboard()

    for cf, data in raw_formats.items():
        if cf == CF_BITMAP:
            user32.SetClipboardData(CF_BITMAP, data)
        elif cf in (CF_DIB, CF_DIBV5):
            size = len(data)
            h = kernel32.GlobalAlloc(0x0002, size)  # GMEM_MOVEABLE
            p = kernel32.GlobalLock(h)
            ctypes.memmove(p, data, size)
            kernel32.GlobalUnlock(h)
            user32.SetClipboardData(cf, h)

    # Add text path (UTF-16-LE, null-terminated)
    encoded = text.encode("utf-16-le") + b"\x00\x00"
    h_text = kernel32.GlobalAlloc(0x0002, len(encoded))
    p_text = kernel32.GlobalLock(h_text)
    ctypes.memmove(p_text, encoded, len(encoded))
    kernel32.GlobalUnlock(h_text)
    user32.SetClipboardData(CF_UNICODETEXT, h_text)

    user32.CloseClipboard()


# ── File saving ──────────────────────────────────────────────────────────
def image_hash(img) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return hashlib.md5(buf.getvalue()).hexdigest()


def save_image(img, fmt="png") -> Path:
    _output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filepath = _output_dir / f"{_prefix}{ts}.{fmt}"
    if fmt.lower() in ("jpg", "jpeg") and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.save(filepath, format="JPEG" if fmt.lower() in ("jpg", "jpeg") else fmt.upper())
    return filepath


# ── Once mode ────────────────────────────────────────────────────────────
def once():
    result = get_clipboard_image()
    if result is None:
        print("No image on clipboard. Take a screenshot (Win+Shift+S) or copy an image first.")
        sys.exit(1)

    img_or_path, fmt = result
    if isinstance(img_or_path, Path):
        filepath = img_or_path
        print(f"Clipboard already has an image file: {filepath}")
    else:
        filepath = save_image(img_or_path, fmt)
        print(f"Saved: {filepath}")

    if should_add_text():
        raw = capture_raw_formats()
        if raw:
            set_clipboard_multiformat(raw, str(filepath))
        print("(Ctrl+V in terminal → path | Ctrl+V in chat app → image)")
    else:
        print("(image saved, clipboard unchanged — not in terminal)")


# ── Watch mode ───────────────────────────────────────────────────────────
def watch(silent=False):
    if not acquire_instance_lock():
        print("Snip2Path is already running in another window.")
        print("Close the other window first, or use snip2path (once mode).")
        sys.exit(1)

    if not silent:
        print("Snip2Path daemon started")
        print(f"  Output: {_output_dir}")
        print(f"  Mode:  {'always-text' if _always_text else 'no-text' if _no_text else 'auto-detect'}")
        print("  (Close this window to stop)")
        print("-" * 40)

    last_seq = get_clipboard_seq()
    last_hash = None

    try:
        while True:
            time.sleep(0.3)
            seq = get_clipboard_seq()
            if seq == last_seq:
                continue

            result = get_clipboard_image()
            if result is None:
                last_seq = seq
                continue

            img_or_path, fmt = result

            if isinstance(img_or_path, Path):
                filepath = img_or_path
                if not silent:
                    print(f"[{datetime.now():%H:%M:%S}] file: {filepath.name}")
            else:
                h = image_hash(img_or_path)
                if h == last_hash:
                    last_seq = seq
                    continue
                last_hash = h

                filepath = save_image(img_or_path, fmt)

                proc_name = get_foreground_process_name()
                if should_add_text():
                    raw = capture_raw_formats()
                    if raw:
                        set_clipboard_multiformat(raw, str(filepath))
                    if not silent:
                        print(f"[{datetime.now():%H:%M:%S}] {filepath.name}  ← path (fg: {proc_name})")
                else:
                    if not silent:
                        print(f"[{datetime.now():%H:%M:%S}] {filepath.name}  saved (fg: {proc_name})")

            last_seq = get_clipboard_seq()
    except KeyboardInterrupt:
        if not silent:
            print("\nStopped")


# ── CLI ──────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="snip2path",
        description="Screenshot → Ctrl+V pastes path in terminal, image in chat apps",
    )
    p.add_argument("-w", "--watch", action="store_true",
                   help="Run in daemon mode: monitor clipboard and auto-process new images")
    p.add_argument("-s", "--silent", action="store_true",
                   help="Suppress output (for background daemon)")
    p.add_argument("-o", "--output-dir", type=str, default=str(DEFAULT_OUTPUT),
                   help=f"Output directory for saved images (default: {DEFAULT_OUTPUT})")
    p.add_argument("-p", "--prefix", type=str, default=DEFAULT_PREFIX,
                   help=f"Filename prefix (default: {DEFAULT_PREFIX})")
    p.add_argument("--always-text", action="store_true",
                   help="Always append text path to clipboard (ignore window detection)")
    p.add_argument("--no-text", action="store_true",
                   help="Never modify clipboard (save image only)")
    p.add_argument("-v", "--version", action="version", version=f"snip2path {VERSION}")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    global _output_dir, _prefix, _always_text, _no_text
    _output_dir = Path(args.output_dir)
    _prefix = args.prefix
    _always_text = args.always_text
    _no_text = args.no_text

    if args.watch:
        watch(silent=args.silent)
    else:
        once()


if __name__ == "__main__":
    main()
