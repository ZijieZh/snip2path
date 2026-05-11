# -*- coding: utf-8 -*-
"""Snip2Path — Screenshot to clipboard path bridge

Cross-platform: Windows + macOS

After screenshot:
  Ctrl+V in terminal    → pastes image file path
  Ctrl+V in browser     → image only (Windows) / path (macOS)
  Ctrl+V in WeChat      → image only

Windows uses Win32 multi-format clipboard (CF_DIB, CF_HDROP).
macOS uses NSPasteboard with UTI (public.png, public.utf8-plain-text).

Usage:
  snip2path              # once: save current clipboard image
  snip2path --watch      # daemon: monitor clipboard continuously
  snip2path -o ~/Screenshots  # custom output directory
"""
import sys
import os
import hashlib
import time
import argparse
import tempfile
from io import BytesIO
from datetime import datetime
from pathlib import Path
from PIL import Image

VERSION = "1.3.0"
DEFAULT_OUTPUT = Path.home() / "Pictures" / "Snip2Path"
DEFAULT_PREFIX = "snip_"

PLATFORM = sys.platform

# ═══════════════════════════════════════════════════════════════════════
# Platform-specific clipboard API
# ═══════════════════════════════════════════════════════════════════════

if PLATFORM == "win32":
    import ctypes
    import struct
    from PIL import ImageGrab

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    gdi32 = ctypes.windll.gdi32

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
    user32.CopyImage.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int,
                                 ctypes.c_int, ctypes.c_uint]
    user32.CopyImage.restype = ctypes.c_void_p

    CF_TEXT = 1
    CF_BITMAP = 2
    CF_DIB = 8
    CF_UNICODETEXT = 13
    CF_HDROP = 15
    CF_DIBV5 = 17

    _mutex_handle = None

    def get_clipboard_seq():
        return user32.GetClipboardSequenceNumber()

    def has_clipboard_text():
        return bool(
            user32.IsClipboardFormatAvailable(CF_UNICODETEXT)
            or user32.IsClipboardFormatAvailable(CF_TEXT)
        )

    def acquire_instance_lock():
        global _mutex_handle
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool,
                                          ctypes.c_wchar_p]
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        kernel32.GetLastError.restype = ctypes.c_uint32
        ERROR_ALREADY_EXISTS = 183
        h = kernel32.CreateMutexW(None, False,
                                  "Global\\Snip2Path_Watch_Mutex")
        _mutex_handle = h
        return not (h and kernel32.GetLastError() == ERROR_ALREADY_EXISTS)

    def get_clipboard_image():
        try:
            img = ImageGrab.grabclipboard()
        except Exception:
            return None
        if img is None:
            return None
        if isinstance(img, list):
            for f in img:
                p = Path(str(f))
                if p.suffix.lower() in IMAGE_EXTS:
                    return p, p.suffix[1:]
            return None
        if hasattr(img, "save"):
            return img, "png"
        return None

    def capture_raw_formats():
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

    def make_hdrop(filepath):
        path_wide = filepath + "\x00"
        file_list = path_wide.encode("utf-16-le") + b"\x00\x00"
        dropfiles = struct.pack("<Iiiii", 20, 0, 0, 0, 1)
        return dropfiles + file_list

    def set_clipboard_multiformat(raw_formats, filepath, with_text=False):
        user32.OpenClipboard(0)
        user32.EmptyClipboard()
        for cf, data in raw_formats.items():
            if cf == CF_BITMAP:
                user32.SetClipboardData(CF_BITMAP, data)
            elif cf in (CF_DIB, CF_DIBV5):
                size = len(data)
                h = kernel32.GlobalAlloc(0x0002, size)
                p = kernel32.GlobalLock(h)
                ctypes.memmove(p, data, size)
                kernel32.GlobalUnlock(h)
                user32.SetClipboardData(cf, h)
        hdrop_data = make_hdrop(filepath)
        h_hdrop = kernel32.GlobalAlloc(0x0002, len(hdrop_data))
        p_hdrop = kernel32.GlobalLock(h_hdrop)
        ctypes.memmove(p_hdrop, hdrop_data, len(hdrop_data))
        kernel32.GlobalUnlock(h_hdrop)
        user32.SetClipboardData(CF_HDROP, h_hdrop)
        if with_text:
            encoded = filepath.encode("utf-16-le") + b"\x00\x00"
            h_text = kernel32.GlobalAlloc(0x0002, len(encoded))
            p_text = kernel32.GlobalLock(h_text)
            ctypes.memmove(p_text, encoded, len(encoded))
            kernel32.GlobalUnlock(h_text)
            user32.SetClipboardData(CF_UNICODETEXT, h_text)
        user32.CloseClipboard()

elif PLATFORM == "darwin":
    from Cocoa import NSPasteboard
    from Foundation import NSData
    import fcntl

    _lock_fd = None
    _pb = None

    def _get_pasteboard():
        global _pb
        if _pb is None:
            _pb = NSPasteboard.generalPasteboard()
        return _pb

    def get_clipboard_seq():
        return _get_pasteboard().changeCount()

    def has_clipboard_text():
        types = _get_pasteboard().types()
        if types is None:
            return False
        return "public.utf8-plain-text" in types

    def acquire_instance_lock():
        global _lock_fd
        lock_file = Path(tempfile.gettempdir()) / "snip2path.lock"
        _lock_fd = open(str(lock_file), "w")
        try:
            fcntl.flock(_lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (OSError, IOError):
            _lock_fd.close()
            _lock_fd = None
            return False

    def _image_from_pb(data):
        return Image.open(BytesIO(bytes(data)))

    def get_clipboard_image():
        pb = _get_pasteboard()
        data = pb.dataForType_("public.png")
        if data:
            return _image_from_pb(data), "png"
        for uti in ("public.tiff", "public.jpeg"):
            data = pb.dataForType_(uti)
            if data:
                return _image_from_pb(data), uti.split(".")[-1]
        return None

    def capture_raw_formats():
        pb = _get_pasteboard()
        raw = {}
        for uti in ("public.png", "public.tiff", "public.jpeg"):
            data = pb.dataForType_(uti)
            if data:
                raw[uti] = bytes(data)
        return raw

    def set_clipboard_multiformat(raw_formats, filepath, with_text=False):
        pb = _get_pasteboard()
        pb.clearContents()
        for uti in ("public.png", "public.tiff", "public.jpeg"):
            if uti in raw_formats:
                img_bytes = raw_formats[uti]
                ns_data = NSData.dataWithBytes_length_(img_bytes, len(img_bytes))
                pb.setData_forType_(ns_data, uti)
                break
        pb.setString_forType_(filepath, "public.utf8-plain-text")

else:
    raise RuntimeError("Unsupported platform: " + PLATFORM)

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"}

# ═══════════════════════════════════════════════════════════════════════
# Shared logic
# ═══════════════════════════════════════════════════════════════════════

_output_dir = DEFAULT_OUTPUT
_prefix = DEFAULT_PREFIX
_with_text = False
_no_clipboard = False


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
    save_fmt = "JPEG" if fmt.lower() in ("jpg", "jpeg") else fmt.upper()
    img.save(filepath, format=save_fmt)
    return filepath


def once():
    if has_clipboard_text():
        print("Clipboard contains text, not an image. Skipping.")
        sys.exit(0)

    result = get_clipboard_image()
    if result is None:
        print("No image on clipboard. Take a screenshot first.")
        sys.exit(1)

    img_or_path, fmt = result
    if isinstance(img_or_path, Path):
        filepath = img_or_path
        print(f"Clipboard already has an image file: {filepath}")
    else:
        filepath = save_image(img_or_path, fmt)
        print(f"Saved: {filepath}")

    if _no_clipboard:
        print("(saved only, clipboard unchanged)")
    else:
        raw = capture_raw_formats()
        if raw:
            set_clipboard_multiformat(raw, str(filepath), with_text=_with_text)
        print("(Ctrl+V in terminal → path | Ctrl+V elsewhere → image)")


def watch(silent=False):
    if not acquire_instance_lock():
        print("Snip2Path is already running in another window.")
        print("Close the other instance first, or use snip2path (once mode).")
        sys.exit(1)

    if not silent:
        print("Snip2Path daemon started")
        print(f"  Output: {_output_dir}")
        if _no_clipboard:
            print("  Mode:  no-clipboard")
        elif _with_text:
            print("  Mode:  path+text")
        else:
            print("  Mode:  path")
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

            if has_clipboard_text():
                last_seq = seq
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

                if _no_clipboard:
                    if not silent:
                        print(f"[{datetime.now():%H:%M:%S}] {filepath.name}  saved")
                else:
                    raw = capture_raw_formats()
                    if raw:
                        set_clipboard_multiformat(raw, str(filepath),
                                                   with_text=_with_text)
                    if not silent:
                        mode = "path+text" if _with_text else "path"
                        print(f"[{datetime.now():%H:%M:%S}] {filepath.name}  ← {mode}")

            last_seq = get_clipboard_seq()
    except KeyboardInterrupt:
        if not silent:
            print("\nStopped")


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
    p.add_argument("--with-text", action="store_true",
                   help="Also add text path (old terminals / macOS)")
    p.add_argument("--no-clipboard", action="store_true",
                   help="Save image only, do not modify clipboard")
    p.add_argument("-v", "--version", action="version",
                   version=f"snip2path {VERSION}")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    global _output_dir, _prefix, _with_text, _no_clipboard
    _output_dir = Path(args.output_dir)
    _prefix = args.prefix
    _with_text = args.with_text
    _no_clipboard = args.no_clipboard

    if args.watch:
        watch(silent=args.silent)
    else:
        once()


if __name__ == "__main__":
    main()
