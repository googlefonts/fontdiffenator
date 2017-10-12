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
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('font_a')
    parser.add_argument('font_b')
    parser.add_argument('-ol', '--output-lines', type=int, default=50)
    args = parser.parse_args()

    comparison = diff_fonts(
        args.font_a,
        args.font_b,
        rendered_diffs=False
    )
    
    output_lines = args.output_lines if args.output_lines else 1000
    cli_report(args.font_a, args.font_b, comparison, output_lines)


def cli_report(font_a, font_b, comp_data, output_lines=10):
    """Generate a report wip"""
    # TODO (m4rc1e): turn into decent report with good formatting.
    print '%s vs %s' % (font_a, font_b)
    for category in comp_data:
        for sub_category in comp_data[category]:
            if comp_data[category][sub_category]:
                print '\n***%s %s %s***' % (
                    category, len(comp_data[category][sub_category]), sub_category
                )
                for comp in comp_data[category][sub_category][:output_lines]:
                    print comp
            else:
                print '\n***%s %s***' % (category, sub_category)
                print 'No differences'


if __name__ == '__main__':
    main()
