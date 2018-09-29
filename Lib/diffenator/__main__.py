# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Font Diffenator
~~~~~~~~~~~~~~~

Report differences between two fonts.

Diffs can be made for the following categories, names, marks, mkmks,
attribs, metrics, glyphs and kerns.

Examples
--------
Diff everything:
diffenator /path/to/font_a.ttf /path/to/font_b.ttf

Diff just a nametable:
diffenator /path/to/font_a.ttf /path/to/font_b.ttf -td names

Diff nametable and marks:
diffenator /path/to/font_a.ttf /path/to/font_b.ttf -td names marks

Output report as markdown:
diffenator /path/to/font_a.ttf /path/to/font_b.ttf -md

Diff kerning and ignore differences under 30 units:
diffenator /path/to/font_a.ttf /path/to/font_b.ttf -td kerns --kerns_thresh 30

Diff rendered glyphs:
diffenator /path/to/font_a.ttf /path/to/font_b.ttf -td glyphs -rd
"""
from argparse import RawTextHelpFormatter
from diffenator.diff import diff_fonts
from diffenator import __version__
from diffenator.font import InputFont
from diffenator.utils import (
    vf_instance,
    vf_instance_from_static
)
from diffenator.reporters import diff_report, CLIFormatter, MDFormatter
import argparse


DIFF_CHOICES = [
    'names',
    'marks',
    'mkmks',
    'attribs',
    'metrics',
    'glyphs',
    'kerns'
]


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument('--version', action='version', version=__version__)

    parser.add_argument('font_a')
    parser.add_argument('font_b')
    parser.add_argument('-td', '--to_diff', nargs='+', choices=DIFF_CHOICES,
                        default='*',
                        help="categories to diff. '*'' diffs everything")

    parser.add_argument('-ol', '--output-lines', type=int, default=50,
                        help="Amout of diffs to report for each diff table")
    parser.add_argument('-md', '--markdown', action='store_true',
                        help="Output report as markdown.")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Report diffs which are the same')

    parser.add_argument('-i', '--vf-instance', default='Regular',
                        help='Variable font instance to diff')

    parser.add_argument('--marks_thresh', type=int, default=0,
                        help="Ignore modified marks under this value")
    parser.add_argument('--mkmks_thresh', type=int, default=0,
                        help="Ignore modified mkmks under this value")
    parser.add_argument('--kerns_thresh', type=int, default=0,
                        help="Ignore modified kerns under this value")
    parser.add_argument('--glyphs_thresh', type=float, default=0,
                        help="Ignore modified glyphs under this value")
    parser.add_argument('-r', '--render_diffs', action='store_true',
                        help=("Render glyphs with harfbuzz and compare "
                              "pixel diffs."))
    args = parser.parse_args()

    font_a = InputFont(args.font_a)
    font_b = InputFont(args.font_b)

    if 'fvar' in font_a and 'fvar' not in font_b:
        font_a = vf_instance_from_static(font_a, font_b)

    elif 'fvar' not in font_a and 'fvar' in font_b:
        font_b = vf_instance_from_static(font_b, font_a)

    elif 'fvar' in font_a and 'fvar' in font_b:
        font_a = vf_instance(font_a, args.vf_instance)
        font_b = vf_instance(font_b, args.vf_instance)

    diff = diff_fonts(
        font_a,
        font_b,
        categories_to_diff=args.to_diff,
        glyph_threshold=args.glyphs_thresh,
        marks_threshold=args.marks_thresh,
        mkmks_threshold=args.mkmks_thresh,
        kerns_threshold=args.kerns_thresh,
        render_diffs=args.render_diffs
    )

    report_formatter = CLIFormatter if not args.markdown else MDFormatter
    report = diff_report(
        diff,
        args.font_a,
        args.font_b,
        Formatter=report_formatter,
        output_lines=args.output_lines,
        verbose=args.verbose
    )
    print(report)


if __name__ == '__main__':
    main()
