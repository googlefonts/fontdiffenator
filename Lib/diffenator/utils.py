import os


def cli_reporter(font_a, font_b, comp_data, output_lines=10):
    """Generate a report wip"""
    print '%s vs %s' % (os.path.basename(font_a), os.path.basename(font_b))
    for category in comp_data:
        for sub_category in comp_data[category]:
            if comp_data[category][sub_category]:
                print '\n***%s %s %s***' % (
                    category, len(comp_data[category][sub_category]), sub_category
                )
                if category == 'attribs' and sub_category == 'modified':
                    print dict_cli_table(
                        comp_data[category][sub_category][:output_lines],
                        ['table', 'attrib', 'value_a', 'value_b']
                    )
                elif category == 'metrics' and sub_category == 'modified':
                    print dict_cli_table(
                        comp_data[category][sub_category][:output_lines],
                        ['glyph', 'diff_adv', 'diff_lsb', 'diff_rsb']
                    )
                elif category == 'kern' and sub_category == 'modified':
                    print dict_cli_table(
                        comp_data[category][sub_category][:output_lines],
                        ['left', 'right', 'diff']
                    )
                elif category == 'kern':
                    print dict_cli_table(
                        comp_data[category][sub_category][:output_lines],
                        ['left', 'right', 'value']
                    )
                elif category == 'marks' and sub_category == 'modified':
                    print dict_cli_table(
                        comp_data[category][sub_category][:output_lines],
                        ['base_glyph', 'mark_glyph', 'diff_x', 'diff_y']
                    )
                elif category == 'marks':
                    print dict_cli_table(
                        comp_data[category][sub_category][:output_lines],
                        ['base_glyph', 'mark_glyph', 'base_x',
                         'base_y', 'mark_x', 'mark_y']
                    )
                elif category == 'glyphs':
                    print dict_cli_table(
                        comp_data[category][sub_category][:output_lines],
                        ['glyph']
                    )
                elif category == 'names' and sub_category == 'modified':
                    print dict_cli_table(
                        comp_data[category][sub_category][:output_lines],
                        ['id', 'string_a', 'string_b'],
                        clip_col=True
                    )
                elif category == 'names' and (sub_category == 'new' or \
                                              sub_category == 'missing'):
                    print dict_cli_table(
                        comp_data[category][sub_category][:output_lines],
                        ['id', 'string'],
                    )
                else:
                    print dict_cli_table(comp_data[category][sub_category][:output_lines])
            else:
                print '\n***%s %s***' % (category, sub_category)
                print 'No differences'


def dict_cli_table(l, columns=None, clip_col=False):
    """Output a cli friendly table from a list of dicts"""
    if not columns:
        columns = l[0].keys()
    t_format = "{:<20}" * len(columns)
    table = []
    table.append(t_format.format(*tuple(columns)))
    for row in l:
        assembled = []
        for h in columns:
            cell = row[h]
            if clip_col and len(cell) >= 19:
                cell = row[h][:16] + '...'
            assembled.append(cell)
        table.append(t_format.format(*tuple(assembled)))
    return '\n'.join(table)
