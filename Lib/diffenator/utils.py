import os


def cli_reporter(font_a, font_b, comp_data, output_lines=10):
    """Generate a cli report"""
    column_mapping = {
        ('attribs', 'modified'): ['table', 'attrib', 'value_a', 'value_b'],
        ('metrics', 'modified'): ['glyph', 'diff_adv', 'diff_lsb', 'diff_rsb'],
        ('kern', 'modified'): ['left', 'right', 'diff'],
        ('kern', 'new'): ['left', 'right', 'value'],
        ('kern', 'missing'): ['left', 'right', 'value'],
        ('marks', 'modified'): ['base_glyph', 'mark_glyph', 'diff_x', 'diff_y'],
        ('marks', 'new'): ['base_glyph', 'mark_glyph', 'base_x',
                           'base_y', 'mark_x', 'mark_y'],
        ('marks', 'missing'): ['base_glyph', 'mark_glyph', 'base_x',
                               'base_y', 'mark_x', 'mark_y'],
        ('glyphs', 'modified'): ['glyph', 'diff'],
        ('glyphs', 'new'): ['glyph'],
        ('glyphs', 'missing'): ['glyph'],
        ('names', 'modified'): ['id', 'string_a', 'string_b'],
        ('names', 'new'): ['id', 'string'],
        ('names', 'missing'): ['id', 'string'],
    }
    report = []
    report.append(
        '%s vs %s' % (os.path.basename(font_a), os.path.basename(font_b))
    )
    for category in comp_data:
        for sub_category in comp_data[category]:
            if comp_data[category][sub_category]:
                report.append(
                    '\n\n***%s %s %s***\n' % (
                        category,
                        len(comp_data[category][sub_category]),
                        sub_category
                    )
                )
                report.append(
                    dict_cli_table(
                        comp_data[category][sub_category][:output_lines],
                        column_mapping[(category, sub_category)],
                        clip_col=20)
                )
            else:
                report.append('\n\n***%s %s***\n' % (category, sub_category))
                report.append('No differences')
    return ''.join(report)


def dict_cli_table(l, columns=None, clip_col=False):
    """Output a cli friendly table from a list of dicts"""
    if not columns:
        columns = l[0].keys()
    t_format = unicode("{:<20}" * len(columns))
    table = []
    table.append(t_format.format(*tuple(columns)))
    for row in l:
        assembled = []
        for h in columns:
            cell = unicode(row[h])
            if clip_col and len(cell) >= 19:
                cell = cell[:16] + '...'
            assembled.append(cell)
        table.append(t_format.format(*tuple(assembled)))
    return '\n'.join(table)
