"""Functional tests

Test will produce the following tuple of all path permutations

paths = ['path/to/font_a', 'path/to/font_b']

[
    (path/to/font_a, path/to/font_b),
    (path/to/font_b, path/to/font_a),
]

and run them through our main DiffFonts functions.

This test is slow and should be run on challenging fonts.
"""
from diffenator.diff import DiffFonts
from diffenator.font import DFont
from itertools import permutations
import collections
from glob import glob
import os
import unittest
import tempfile


class TestFunctionality(unittest.TestCase):

    def setUp(self):
        self._path = os.path.dirname(__file__)
        font_paths = glob(os.path.join(self._path, 'data', '*.ttf'))
        self.font_path_combos = permutations(font_paths, r=2)

    def test_diff(self):
        for font_a_path, font_b_path in self.font_path_combos:
            font_a = DFont(font_a_path)
            font_b = DFont(font_b_path)
            diff = DiffFonts(font_a, font_b)
            with tempfile.TemporaryDirectory() as gif_dir:
                diff.to_gifs(gif_dir)
                self.assertNotEqual(len(os.listdir(gif_dir)), 0)
            self.assertNotEqual(diff, collections.defaultdict(dict))

    def test_diff_vf_vs_static(self):
        font_a_path = os.path.join(self._path, 'data', 'vf_test', 'Fahkwang-VF.ttf')
        font_b_path = os.path.join(self._path, 'data', 'vf_test', 'Fahkwang-Light.ttf')
        font_a = DFont(font_a_path)
        font_b = DFont(font_b_path)

        font_a.set_variations({"wght": 300})
        diff = DiffFonts(font_a, font_b)
        self.assertNotEqual(diff, collections.defaultdict(dict))


class TestVisualize(unittest.TestCase):
    def test_viz(self):
        font_path = os.path.join(os.path.dirname(__file__), "data", "Play-Regular.ttf")
        font = DFont(font_path)
        img = font.glyphs.to_png(limit=10000)
        self.assertNotEqual(img, None)


if __name__ == '__main__':
    unittest.main()
