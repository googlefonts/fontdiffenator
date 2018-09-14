"""Module for report generators and objects used to create reports"""
import sys
if sys.version_info.major == 3:
    unicode = str

__all__ = ['CLIFormatter', 'MDFormatter']


class Formatter:
    """Base Class for formatters"""
    def __init__(self):
        self.report = []

    def heading(self, string):
        raise NotImplementedError()

    def subheading(self, string):
        raise NotImplementedError()

    def subsubheading(self, string):
        raise NotImplementedError()

    def table_heading(self, row):
        raise NotImplementedError()

    def table_row(self, row, clip_col=True):
        raise NotImplementedError()

    def linebreak(self):
        self.report.append('')

    def paragraph(self, string):
        self.report.append(string)

    @property
    def text(self):
        return '\n'.join(self.report)


class CLIFormatter(Formatter):
    """Formatter for CommandLines."""
    def heading(self, string):
        self.report.append('**{}**\n'.format(string))

    def subheading(self, string):
        self.report.append('***{}***\n'.format(string))

    def subsubheading(self, string):
        self.report.append('****{}****\n'.format(string))

    def table_heading(self, row, order=None):
        if not order:
            order = row.keys()
        header = unicode("{:<20}" * len(order))
        header = header.format(*tuple(order))
        self.report.append(header)

    def table_row(self, row, order=None, clip_col=True):
        if not order:
            order = row.keys()
        assembled = []
        t_format = unicode("{:<20}" * len(order))
        for k in order:
            cell = unicode(row[k])
            if clip_col and len(cell) >= 19:
                cell = cell[:16] + '...'
            assembled.append(cell)
        row = t_format.format(*tuple(assembled))
        self.report.append(row)


class MDFormatter(Formatter):
    """Formatter for Github Markdown"""
    def heading(self, string):
        self.report.append('# {}\n'.format(string))

    def subheading(self, string):
        self.report.append('## {}\n'.format(string))

    def subsubheading(self, string):
        self.report.append('### {}\n'.format(string))

    def table_heading(self, row, order=None):
        if not order:
            order = list(row.keys())
        string = ' | '.join(order)
        string += '\n'
        string += '--- | ' * len(order)
        self.report.append(string)

    def table_row(self, row, order=None):
        if not order:
            order = list(row.keys())
        assembled = []
        for k in order:
            cell = unicode(row[k])
            assembled.append(cell)
        string = ' | '.join(assembled)
        self.report.append(string)


DIFF_ORDER = [
    'attribs',
    'names',
    'glyphs',
    'metrics',
    'marks',
    'mkmk',
    'kerns'
]

REPORT_COLUMNS = {
    ('attribs', 'modified'): ['table', 'attrib', 'value_a', 'value_b'],

    ('metrics', 'modified'): ['glyph', 'diff_adv', 'diff_lsb', 'diff_rsb'],

    ('kerns', 'modified'): ['left', 'right', 'diff'],
    ('kerns', 'new'): ['left', 'right', 'value'],
    ('kerns', 'missing'): ['left', 'right', 'value'],

    ('marks', 'modified'): ['base_glyph', 'mark_glyph', 'diff_x', 'diff_y'],
    ('marks', 'new'): ['base_glyph', 'mark_glyph', 'base_x',
                       'base_y', 'mark_x', 'mark_y'],
    ('marks', 'missing'): ['base_glyph', 'mark_glyph', 'base_x',
                           'base_y', 'mark_x', 'mark_y'],

    ('mkmks', 'modified'): ['base_glyph', 'mark_glyph', 'diff_x', 'diff_y'],
    ('mkmks', 'new'): ['base_glyph', 'mark_glyph', 'base_x',
                       'base_y', 'mark_x', 'mark_y'],
    ('mkmks', 'missing'): ['base_glyph', 'mark_glyph', 'base_x',
                           'base_y', 'mark_x', 'mark_y'],

    ('glyphs', 'modified'): ['glyph', 'diff'],
    ('glyphs', 'new'): ['glyph'],
    ('glyphs', 'missing'): ['glyph'],

    ('names', 'modified'): ['id', 'string_a', 'string_b'],
    ('names', 'new'): ['id', 'string'],
    ('names', 'missing'): ['id', 'string'],
}


def diff_report(diff_dict, font_a_path, font_b_path, Formatter=CLIFormatter,
                output_lines=50, verbose=False):
    """Generate a report from a diff_fonts object

    Parameters
    ----------
    diff_dict: list
        A diffenator.diff.diff_font object
    Formatter: Formatter
        Text formatter to use for report
    output_lines: int
        How many rows to display for each diff table
    verbose: bool
        If True, include 'empty' message if no diffs are found for a diff table

    Returns
    -------
    str
    """
    report = Formatter()

    report.heading('Diffenator')
    report.subheading('{} vs {}'.format(font_a_path, font_b_path))

    for category in DIFF_ORDER:
        if category not in diff_dict:
            continue
        for sub_category in ['new', 'missing', 'modified']:
            if sub_category not in diff_dict[category]:
                continue

            diff_table = diff_dict[category][sub_category]
            diff_title = "{} {}".format(category.title(), sub_category.title())

            if diff_table:
                report.subsubheading("{}: {}".format(diff_title, len(diff_table)))
                report.table_heading(
                    diff_table[0], order=REPORT_COLUMNS[(category, sub_category)])
                for row in diff_table[:output_lines]:
                    report.table_row(row, order=REPORT_COLUMNS[(category, sub_category)])
                report.linebreak()
            elif verbose:
                report.subsubheading(diff_title)
                report.paragraph("No differences")
                report.linebreak()
    return report.text


def dump_report(table, table_name, Formatter=CLIFormatter,
                strings_only=False):
    """Generate a report for a dumped font table.

    Parameters
    ----------
    table: list
        A dumped font table produced by a dump function e.g
        table = dump_kerning(font)
    table_name: str
        Name of table which is being dumped. Used in report only
    Formatter: Formatter
        Text formatter to use for report
    String_only: bool
        If True only return the character combos.

    Returns
    -------
    str
    """
    report = Formatter()

    report.heading('Dumper')
    report.subheading('{}'.format('font_a'))
    report.subsubheading(table_name)

    if strings_only and table_name in (
        'kerns', 'marks', 'mkmks', 'glyphs', 'metrics'
    ):
        string = ' '.join([r['string'] for r in table])
        report.paragraph(string)
    else:
        cols = table[0]
        for ignore_column in ('description', 'features'):
            if ignore_column in cols:
                del cols[ignore_column]
        cols = cols
        report.table_heading(cols)
        for row in table:
            report.table_row(row, order=cols)
    return report.text
