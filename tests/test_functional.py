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
from diffenator.font import InputFont
from diffenator.utils import vf_instance
from itertools import permutations
import collections
from glob import glob
import os
import unittest


class TestFunctionality(unittest.TestCase):

    def setUp(self):
        self._path = os.path.dirname(__file__)
        font_paths = glob(os.path.join(self._path, 'data', '*.ttf'))
        self.font_path_combos = permutations(font_paths, r=2)

    def test_diff(self):
        for font_a_path, font_b_path in self.font_path_combos:
            font_a = InputFont(font_a_path)
            font_b = InputFont(font_b_path)
            diff = diff_fonts(font_a, font_b)
            self.assertNotEqual(diff, collections.defaultdict(dict))

    def test_diff_vf_vs_static(self):
        font_a_path = os.path.join(self._path, 'data', 'vf_test', 'Fahkwang-VF.ttf')
        font_b_path = os.path.join(self._path, 'data', 'vf_test', 'Fahkwang-Light.ttf')
        font_a = InputFont(font_a_path)
        font_b = InputFont(font_b_path)

        font_a = vf_instance(font_a, 'Light')
        diff = diff_fonts(font_a, font_b)
        self.assertNotEqual(diff, collections.defaultdict(dict))


if __name__ == '__main__':
    unittest.main()
