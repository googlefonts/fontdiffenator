"""Functional tests

Test will produce the following tuple of all path permutations

paths = ['path/to/font_a', 'path/to/font_b']

[
    (path/to/font_a, path/to/font_b),
    (path/to/font_b, path/to/font_a),
]

and run them through our main diff_fonts functions.

This test is slow and should be run on challenging fonts.
"""
from diffenator.diff import diff_fonts
from itertools import permutations
import collections
from glob import glob
import os
import unittest


class TestFunctionality(unittest.TestCase):

    def setUp(self):
        _path = os.path.dirname(__file__)
        font_paths = glob(os.path.join(_path, 'data', '*.ttf'))
        self.font_path_combos = permutations(font_paths, r=2)

    def test_diff(self):
        for font_a_path, font_b_path in self.font_path_combos:
            diff = diff_fonts(font_a_path, font_b_path)
            self.assertNotEqual(diff, collections.defaultdict(dict))


if __name__ == '__main__':
    unittest.main()
