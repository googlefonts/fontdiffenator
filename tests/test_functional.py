"""Functional tests

Test will produce the following tuple of all path permutations

paths = ['path/to/font_a', 'path/to/font_b']

[
    (path/to/font_a, path/to/font_b),
    (path/to/font_b, path/to/font_a),
]

This test is slow and should be run on challenging fonts.
"""
from diffenator import CHOICES
from itertools import permutations
import subprocess
from glob import glob
import os
import unittest
import tempfile
import shutil

class TestFunctionality(unittest.TestCase):

    def setUp(self):
        self._path = os.path.dirname(__file__)
        font_paths = glob(os.path.join(self._path, 'data', '*.ttf'))
        self.font_path_combos = permutations(font_paths, r=2)
        cbdt_font_paths = glob(os.path.join(self._path, 'data', 'cbdt_test', '*.ttf'))
        self.cbdt_font_path_combos = permutations(cbdt_font_paths, r=2)

    def test_diff(self):
        for font_a_path, font_b_path in self.font_path_combos:
            gif_dir = tempfile.mktemp()
            subprocess.call([
                "diffenator",
                font_a_path,
                font_b_path,
                "-r", gif_dir])
            gifs = [f for f in os.listdir(gif_dir) if f.endswith(".gif")]
            self.assertNotEqual(gifs, [])
            shutil.rmtree(gif_dir)

    def test_cbdt_diff(self):
        for font_a_path, font_b_path in self.cbdt_font_path_combos:
            gif_dir = tempfile.mktemp()
            subprocess.call([
                "diffenator",
                font_a_path,
                font_b_path,
                "-r", gif_dir])
            gifs = [f for f in os.listdir(gif_dir) if f.endswith(".gif")]
            self.assertNotEqual(gifs, [])
            shutil.rmtree(gif_dir)

    def test_diff_vf_vs_static(self):
        font_a_path = os.path.join(self._path, 'data', 'vf_test', 'Fahkwang-VF.ttf')
        font_b_path = os.path.join(self._path, 'data', 'vf_test', 'Fahkwang-Light.ttf')
        cmd = subprocess.check_output([
            "diffenator",
            font_a_path,
            font_b_path
        ])

        self.assertNotEqual(cmd, None)

    def test_cbdt_dump(self):
        font_path = os.path.join(self._path, 'data', 'cbdt_test', 'NotoColorEmoji-u11-u1F349.ttf')
        for category in CHOICES:
            cmd = subprocess.check_output([
                "dumper",
                font_path,
                category,
            ])
            self.assertNotEqual(cmd, None)

    def test_dump(self):
        font_path = os.path.join(self._path, 'data', 'Play-Regular.ttf')
        for category in CHOICES:
            cmd = subprocess.check_output([
                "dumper",
                font_path,
                category,
            ])
            self.assertNotEqual(cmd, None)


if __name__ == '__main__':
    unittest.main()
