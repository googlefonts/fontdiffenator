"""Dump a font's table"""
import argparse
from font import InputFont
from kerning import dump_gpos_kerning
from marks import DumpMarks
from attribs import dump_attribs
from names import dump_nametable
from metrics import dump_glyph_metrics
from glyphs import dump_glyphs
from utils import dict_table


DUMP_FUNC = {
    'kerns': dump_gpos_kerning,
    'attribs': dump_attribs,
    'names': dump_nametable,
    'metrics': dump_glyph_metrics,
    'glyphs': dump_glyphs
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('font')
    parser.add_argument('dump', choices=DUMP_FUNC.keys() + ['marks', 'mkmks'])
    parser.add_argument('-s', '--strings-only', action='store_true')
    parser.add_argument('-ol', '--output-lines', type=int)
    parser.add_argument('-md', '--markdown', action='store_true')

    args = parser.parse_args()
    font = InputFont(args.font)
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
            print row['string'],
    else:
        cols = table[0]
        for ignore_column in ('description', 'features'):
            if ignore_column in cols:
                del cols[ignore_column]
        cols = cols.keys()
        print dict_table(table, columns=cols, markdown=markdown)


if __name__ == '__main__':
    main()
