"""
Dumper
~~~~~~

Dump a font category.

Categories which can be dumped are attribs, metrics, kerns, glyphs, names
marks and mkmks.

Examples
--------

Dump kerning:
dumper /path/to/font.ttf kerns

Dump just kerning pair strings:
dumper /path/to/font.ttf kerns -s

Output report as markdown:
dumper /path/to/font.ttf -md
"""
from __future__ import print_function
from argparse import RawTextHelpFormatter
import argparse
import os
from diffenator.font import InputFont
from diffenator.kerning import dump_kerning
from diffenator.marks import DumpMarks
from diffenator.attribs import dump_attribs
from diffenator.names import dump_nametable
from diffenator.metrics import dump_glyph_metrics
from diffenator.glyphs import dump_glyphs
from diffenator.reporters import dump_report, CLIFormatter, MDFormatter
from diffenator.utils import (
    vf_instance,
    vf_instance_from_static
)


DUMP_FUNC = {
    'kerns': dump_kerning,
    'attribs': dump_attribs,
    'names': dump_nametable,
    'metrics': dump_glyph_metrics,
    'glyphs': dump_glyphs
}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument('font')
    parser.add_argument('dump', choices=list(DUMP_FUNC.keys()) + ['marks', 'mkmks'])
    parser.add_argument('-s', '--strings-only', action='store_true')
    parser.add_argument('-ol', '--output-lines', type=int, default=100)
    parser.add_argument('-md', '--markdown', action='store_true')
    parser.add_argument('-i', '--vf-instance',
                        help='Variable font instance to diff')
    parser.add_argument('-r', '--render-path',
            help="Path to generate png to")

    args = parser.parse_args()
    font = InputFont(args.font)

    if 'fvar' in font and args.dump not in ('names', 'attribs') and not args.vf_instance:
        raise Exception("Include a VF instance to dump e.g -i Regular")

    if 'fvar' in font and args.dump not in ('names', 'attribs'):
        font = vf_instance(font, args.vf_instance)

    if args.dump in ('marks', 'mkmks'):
        dump_marks = DumpMarks(font)
        if args.dump == 'marks':
            table = dump_marks.mark_table
        else:
            table = dump_marks.mkmk_table
    else:
        table = DUMP_FUNC[args.dump](font)
    report_len = len(table)
    table = table[:args.output_lines]

    formatter = CLIFormatter if not args.markdown else MDFormatter
    report = dump_report(table, args.dump, Formatter=formatter)
    print(report)
    if args.output_lines < report_len:
        print(("Showing {} out of {} items. Increase the flag -ol "
               "to view more".format(args.output_lines, report_len)))
    if args.render_path:
        from diffenator.visualize import render_table
        render_table(font, table, dst=args.render_path)


if __name__ == '__main__':
    main()
