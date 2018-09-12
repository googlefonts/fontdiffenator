"""Dump a font's table"""
from __future__ import print_function
import argparse
from diffenator.font import InputFont
from diffenator.kerning import dump_kerning
from diffenator.marks import DumpMarks
from diffenator.attribs import dump_attribs
from diffenator.names import dump_nametable
from diffenator.metrics import dump_glyph_metrics
from diffenator.glyphs import dump_glyphs
from diffenator.utils import dict_table, vf_instance


DUMP_FUNC = {
    'kerns': dump_kerning,
    'attribs': dump_attribs,
    'names': dump_nametable,
    'metrics': dump_glyph_metrics,
    'glyphs': dump_glyphs
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('font')
    parser.add_argument('dump', choices=list(DUMP_FUNC.keys()) + ['marks', 'mkmks'])
    parser.add_argument('-s', '--strings-only', action='store_true')
    parser.add_argument('-ol', '--output-lines', type=int)
    parser.add_argument('-md', '--markdown', action='store_true')
    parser.add_argument('-i', '--vf-instance', default='Regular',
                        help='Variable font instance to diff')

    args = parser.parse_args()
    font = InputFont(args.font)

    if 'fvar' in font:
        font = vf_instance(font, args.vf_instance)

    markdown = True if args.markdown else False

    if args.dump in ('marks', 'mkmks'):
        dump_marks = DumpMarks(font)
        if args.dump == 'marks':
            table = dump_marks.mark_table
        else:
            table = dump_marks.mkmk_table
    else:
        table = DUMP_FUNC[args.dump](font)

    table = table[:args.output_lines] if args.output_lines else table

    if args.strings_only and args.dump in (
        'kerns', 'marks', 'mkmks', 'glyphs', 'metrics'
    ):
        for row in table:
            print(row['string']),
    else:
        cols = table[0]
        for ignore_column in ('description', 'features'):
            if ignore_column in cols:
                del cols[ignore_column]
        cols = cols.keys()
        print(dict_table(table, columns=cols, markdown=markdown))


if __name__ == '__main__':
    main()
