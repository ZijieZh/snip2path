# -*- coding: utf-8 -*-
"""Basic tests for snip2path."""
import sys
import os
import unittest
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent.parent))

from snip2path import (
    VERSION,
    save_image,
    image_hash,
    build_parser,
    IMAGE_EXTS,
    CF_BITMAP,
    CF_DIB,
    CF_UNICODETEXT,
    CF_DIBV5,
)
from PIL import Image


class TestConstants(unittest.TestCase):
    def test_version(self):
        self.assertIsInstance(VERSION, str)
        self.assertTrue(len(VERSION) > 0)

    def test_clipboard_format_ids(self):
        self.assertEqual(CF_BITMAP, 2)
        self.assertEqual(CF_DIB, 8)
        self.assertEqual(CF_UNICODETEXT, 13)
        self.assertEqual(CF_DIBV5, 17)

    def test_image_extensions(self):
        self.assertIn(".png", IMAGE_EXTS)
        self.assertIn(".jpg", IMAGE_EXTS)
        self.assertIn(".webp", IMAGE_EXTS)


class TestSaveImage(unittest.TestCase):
    def setUp(self):
        self.img = Image.new("RGB", (100, 50), color="red")
        self.test_dir = Path("C:/AI/snip2path/tests/_test_output")

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

        # Verify it's a valid image
        reloaded = Image.open(filepath)
        self.assertEqual(reloaded.size, (100, 50))

    def test_save_image_jpg_converts_rgba(self):
        import snip2path
        snip2path._output_dir = self.test_dir
        snip2path._prefix = "test_"

        # Create RGBA image
        rgba_img = Image.new("RGBA", (50, 50), color=(255, 0, 0, 128))
        filepath = snip2path.save_image(rgba_img, "jpg")
        self.assertTrue(filepath.exists())
        self.assertEqual(filepath.suffix, ".jpg")
        # Should have been converted to RGB
        reloaded = Image.open(filepath)
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
