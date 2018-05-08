import os


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


def dict_table(l, columns=None, clip_col=False, markdown=False):
    """Output a cli friendly table from a list of dicts"""
    table = []
    if not columns:
        columns = l[0].keys()
    # create table header
    if markdown:
        table += [
            '\n',
            ' | '.join(columns),
            '--- | ' * len(columns)
        ]
    else:
        t_format = unicode("{:<20}" * len(columns))
        header = t_format.format(*tuple(columns))
        table.append(header)

    for row in l:
        if markdown:
            table.append(_assemble_markdown_row(row, columns))
        else:
            table.append(
                _assemble_cli_row(t_format, row, columns, clip_col=clip_col)
            )
    return '\n'.join(table)


def _assemble_markdown_row(row, columns):
    assembled = []
    for h in columns:
        cell = unicode(row[h])
        assembled.append(cell)
    return ' | '.join(assembled)


def _assemble_cli_row(t_format, row, columns, clip_col=False):
    """Output a clie friendly table from a list of dicts"""
    assembled = []
    for h in columns:
        cell = unicode(row[h])
        if clip_col and len(cell) >= 19:
            cell = cell[:16] + '...'
        assembled.append(cell)
    return t_format.format(*tuple(assembled))


def diff_reporter(font_a, font_b, comp_data,
                  markdown=False, output_lines=10, verbose=False):
    """Generate a cli report"""
    report = []
    h1 = '# ' if markdown else ''
    h2 = '## ' if markdown else ''

    title = '{}Diffenator\n'.format(h1)
    subtitle = '{}{} vs {}'.format(
        h2, os.path.basename(font_a), os.path.basename(font_b)
    )
    report.append(title)
    report.append(subtitle)
    for category in comp_data:
        for sub_category in comp_data[category]:
            if comp_data[category][sub_category]:
                report.append(
                    '\n\n**%s %s %s**\n' % (
                        category,
                        len(comp_data[category][sub_category]),
                        sub_category
                    )
                )
                report.append(
                    dict_table(
                        comp_data[category][sub_category][:output_lines],
                        column_mapping[(category, sub_category)],
                        markdown=markdown)
                )
            elif verbose:
                report.append('\n\n**%s %s**\n' % (category, sub_category))
                report.append('No differences')
    return ''.join(report)
