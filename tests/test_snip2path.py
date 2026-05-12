# -*- coding: utf-8 -*-
"""Basic tests for snip2path."""
import sys
import os
import unittest
from pathlib import Path
from io import BytesIO
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import snip2path

from snip2path import (
    VERSION,
    save_image,
    image_hash,
    build_parser,
    IMAGE_EXTS,
    PLATFORM,
)
from PIL import Image

if PLATFORM == "win32":
    from snip2path import (
        make_hdrop,
        CF_BITMAP,
        CF_DIB,
        CF_HDROP,
        CF_UNICODETEXT,
        CF_DIBV5,
    )


class TestConstants(unittest.TestCase):
    def test_version(self):
        self.assertEqual(VERSION, "1.4.0")

    def test_platform(self):
        self.assertIn(PLATFORM, ("win32", "darwin", "linux"))

    def test_image_extensions(self):
        self.assertIn(".png", IMAGE_EXTS)
        self.assertIn(".jpg", IMAGE_EXTS)
        self.assertIn(".webp", IMAGE_EXTS)


class TestSaveImage(unittest.TestCase):
    def setUp(self):
        self.img = Image.new("RGB", (100, 50), color="red")
        self.test_dir = Path(__file__).parent / "_test_output"

    def tearDown(self):
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_save_image_default_fmt(self):
        import snip2path
        snip2path._output_dir = self.test_dir
        snip2path._prefix = "test_"

        filepath = snip2path.save_image(self.img, "png")
        self.assertTrue(filepath.exists())
        self.assertIn("test_", filepath.name)
        self.assertEqual(filepath.suffix, ".png")

        with Image.open(filepath) as reloaded:
            self.assertEqual(reloaded.size, (100, 50))

    def test_save_image_jpg_converts_rgba(self):
        import snip2path
        snip2path._output_dir = self.test_dir
        snip2path._prefix = "test_"

        rgba_img = Image.new("RGBA", (50, 50), color=(255, 0, 0, 128))
        filepath = snip2path.save_image(rgba_img, "jpg")
        self.assertTrue(filepath.exists())
        self.assertEqual(filepath.suffix, ".jpg")
        with Image.open(filepath) as reloaded:
            self.assertEqual(reloaded.mode, "RGB")


class TestImageHash(unittest.TestCase):
    def test_same_image_same_hash(self):
        img1 = Image.new("RGB", (10, 10), color="blue")
        img2 = Image.new("RGB", (10, 10), color="blue")
        self.assertEqual(image_hash(img1), image_hash(img2))

    def test_different_image_different_hash(self):
        img1 = Image.new("RGB", (10, 10), color="blue")
        img2 = Image.new("RGB", (10, 10), color="red")
        self.assertNotEqual(image_hash(img1), image_hash(img2))


class TestCLI(unittest.TestCase):
    def test_parser_defaults(self):
        parser = build_parser()
        args = parser.parse_args([])
        self.assertFalse(args.watch)
        self.assertFalse(args.silent)
        self.assertFalse(args.with_text)
        self.assertFalse(args.no_clipboard)

    def test_parser_watch_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--watch"])
        self.assertTrue(args.watch)

    def test_parser_output_dir(self):
        parser = build_parser()
        args = parser.parse_args(["-o", "C:/test"])
        self.assertEqual(args.output_dir, "C:/test")

    def test_parser_prefix(self):
        parser = build_parser()
        args = parser.parse_args(["-p", "ss_"])
        self.assertEqual(args.prefix, "ss_")

    def test_parser_with_text(self):
        parser = build_parser()
        args = parser.parse_args(["--with-text"])
        self.assertTrue(args.with_text)

    def test_parser_no_clipboard(self):
        parser = build_parser()
        args = parser.parse_args(["--no-clipboard"])
        self.assertTrue(args.no_clipboard)


@unittest.skipUnless(PLATFORM == "win32", "Windows only")
class TestHDROPFormat(unittest.TestCase):
    def test_make_hdrop_starts_with_dropfiles(self):
        data = make_hdrop("C:/test/file.png")
        self.assertEqual(data[0], 20)
        self.assertEqual(data[1], 0)
        self.assertEqual(data[2], 0)
        self.assertEqual(data[3], 0)
        self.assertEqual(data[16], 1)

    def test_make_hdrop_contains_filepath(self):
        data = make_hdrop("C:/test/file.png")
        path_part = data[20:].decode("utf-16-le").rstrip("\x00")
        self.assertEqual(path_part, "C:/test/file.png")


@unittest.skipUnless(PLATFORM == "win32", "Windows only")
class TestClipboardReadMock(unittest.TestCase):
    def test_has_clipboard_text_unicode(self):
        with patch.object(snip2path.user32, "IsClipboardFormatAvailable",
                          side_effect=lambda fmt: fmt == snip2path.CF_UNICODETEXT):
            self.assertTrue(snip2path.has_clipboard_text())

    def test_has_clipboard_text_no_text(self):
        with patch.object(snip2path.user32, "IsClipboardFormatAvailable", return_value=False):
            self.assertFalse(snip2path.has_clipboard_text())

    def test_capture_raw_formats_empty(self):
        with patch.object(snip2path.user32, "OpenClipboard"), \
             patch.object(snip2path.user32, "CloseClipboard"), \
             patch.object(snip2path.user32, "IsClipboardFormatAvailable", return_value=False):
            result = snip2path.capture_raw_formats()
            self.assertEqual(result, {})

    def test_capture_raw_formats_dib(self):
        fake_data = b"\x01\x02\x03\x04"
        with patch.object(snip2path.user32, "OpenClipboard"), \
             patch.object(snip2path.user32, "CloseClipboard"), \
             patch.object(snip2path.user32, "IsClipboardFormatAvailable",
                          side_effect=lambda fmt: fmt == snip2path.CF_DIB), \
             patch.object(snip2path.user32, "GetClipboardData", return_value=0x1234), \
             patch.object(snip2path.kernel32, "GlobalSize", return_value=4), \
             patch.object(snip2path.kernel32, "GlobalLock", return_value=0xABCD), \
             patch.object(snip2path.kernel32, "GlobalUnlock"), \
             patch("snip2path.ctypes.string_at", return_value=fake_data):
            result = snip2path.capture_raw_formats()
            self.assertEqual(result, {snip2path.CF_DIB: fake_data})


@unittest.skipUnless(PLATFORM == "win32", "Windows only")
class TestClipboardWriteMock(unittest.TestCase):
    def test_set_multiformat_sequence(self):
        with patch.object(snip2path.user32, "OpenClipboard") as mock_open, \
             patch.object(snip2path.user32, "EmptyClipboard") as mock_empty, \
             patch.object(snip2path.user32, "SetClipboardData") as mock_set, \
             patch.object(snip2path.user32, "CloseClipboard") as mock_close, \
             patch.object(snip2path.kernel32, "GlobalAlloc", return_value=0x1000), \
             patch.object(snip2path.kernel32, "GlobalLock", return_value=0x2000), \
             patch.object(snip2path.kernel32, "GlobalUnlock"), \
             patch("snip2path.ctypes.memmove"):
            snip2path.set_clipboard_multiformat({}, "C:/test.png", with_text=False)

            mock_open.assert_called_once_with(0)
            mock_empty.assert_called_once()
            mock_close.assert_called_once()
            formats = [call.args[0] for call in mock_set.call_args_list]
            self.assertIn(snip2path.CF_HDROP, formats)

    def test_set_multiformat_with_text(self):
        with patch.object(snip2path.user32, "OpenClipboard"), \
             patch.object(snip2path.user32, "EmptyClipboard"), \
             patch.object(snip2path.user32, "SetClipboardData") as mock_set, \
             patch.object(snip2path.user32, "CloseClipboard"), \
             patch.object(snip2path.kernel32, "GlobalAlloc", return_value=0x1000), \
             patch.object(snip2path.kernel32, "GlobalLock", return_value=0x2000), \
             patch.object(snip2path.kernel32, "GlobalUnlock"), \
             patch("snip2path.ctypes.memmove"):
            snip2path.set_clipboard_multiformat({}, "C:/test.png", with_text=True)

            formats = [call.args[0] for call in mock_set.call_args_list]
            self.assertIn(snip2path.CF_HDROP, formats)
            self.assertIn(snip2path.CF_UNICODETEXT, formats)


if __name__ == "__main__":
    unittest.main(verbosity=2)
