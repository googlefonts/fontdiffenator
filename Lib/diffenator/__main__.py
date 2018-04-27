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
from diff import diff_fonts
from utils import diff_reporter
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('font_a')
    parser.add_argument('font_b')
    parser.add_argument('-ol', '--output-lines', type=int, default=50)
    parser.add_argument('-md', '--markdown', action='store_true',
                        help="Output report as markdown.")
    args = parser.parse_args()

    comparison = diff_fonts(
        args.font_a,
        args.font_b,
    )

    output_lines = args.output_lines if args.output_lines else 1000
    markdown = True if args.markdown else False
    print diff_reporter(args.font_a, args.font_b, comparison,
                        markdown=markdown,
                        output_lines=output_lines)


if __name__ == '__main__':
    main()
