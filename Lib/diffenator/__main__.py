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
from diffenator.diff import diff_fonts
from diffenator import __version__
from diffenator.font import InputFont
from diffenator.utils import (
    diff_reporter,
    vf_instance,
    vf_instance_from_static
)
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('font_a')
    parser.add_argument('font_b')
    parser.add_argument('-ol', '--output-lines', type=int, default=50)
    parser.add_argument('-md', '--markdown', action='store_true',
                        help="Output report as markdown.")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Report diffs which are the same')
    parser.add_argument('-i', '--vf-instance', default='Regular',
                        help='Variable font instance to diff')
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

    comparison = diff_fonts(
        font_a,
        font_b,
    )

    output_lines = args.output_lines if args.output_lines else 1000
    markdown = True if args.markdown else False
    is_verbose = True if args.verbose else False
    report = diff_reporter(args.font_a, args.font_b, comparison,
                        markdown=markdown,
                        output_lines=output_lines,
                        verbose=is_verbose)
    print(report)


if __name__ == '__main__':
    main()
