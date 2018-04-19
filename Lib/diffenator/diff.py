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
"""
Diffs are made in the following manner.

- Dump relevant info for each font into a table.
- For every row in each table, make a key dict from selected columns
- Find matching keys across tables
- Use set operations to find missing and modified rows
- Return a new table including new columns containing the differences


Table structure:
A table is simply a list containing dicts for each row. For this doc,
we'll use the following example:


font_a =
[
    {"glyph" "x", "base_x": 20, "base_y": 40},
    {"glyph" "y", "base_x": 35, "base_y": 40},
]

font_b =
[
    {"glyph" "x", "base_x": 30, "base_y": 40},
    {"glyph" "y", "base_x": 35, "base_y": 40},
    {"glyph" "z", "base_x": 20, "base_y": 40},
]

Making key dict:
In the above tables we can produce a key:

anchors_a_h = {r['glyph']: r for r in table}

{"x" {"glyph" "x", "base_x": 20, "base_y": 40}}
...

We could even make a key by using coords

anchors_a_h = {(r["base_x"], r["base_y"]: r for r in table)}

{(20, 40): {"glyph" "x", "base_x": 20, "base_y": 40}}


This step is similiar to Excel's ability to sort by columns


Returning diff table
When differences are discovered, they're appended to a new table. For
our example we'd get the following:


missing =
[
    {"glyph" "z", "base_x": 20, "base_y": 40}
]

modified =
font_b =
[
    {"glyph" "x", "diff_x": 10, "diff_y": 0},
]

new =
[]
"""

import collections
from font import InputFont
from metrics import dump_glyph_metrics
from kerning import dump_kerning
from attribs import dump_attribs
from names import dump_nametable
from glyphs import dump_glyphs
from marks import DumpMarks
from collections import namedtuple
import time

__all__ = ['diff_fonts', 'diff_metrics', 'diff_kerning',
           'diff_marks', 'diff_attribs', 'diff_glyphs']


DIFF_THRESH = 1057.5000000000025


def timer(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print '%r  %2.2f ms' % \
                  (method.__name__, (te - ts) * 1000)
        return result
    return timed


def diff_fonts(font_a_path, font_b_path, rendered_diffs=False):
    """Compare two fonts and return the difference for:
    Kerning, Marks, Attributes, Metrics and Input sequences.

    rtype: collection.defaultdict"""
    d = collections.defaultdict(dict)

    font_a = InputFont(font_a_path)
    font_b = InputFont(font_b_path)

    comparisons = ['new', 'missing', 'modified']
    diffs = [
        ('kern', diff_kerning(font_a, font_b)),
        ('metrics', diff_metrics(font_a, font_b)),
        ('marks', diff_marks(font_a, font_b)),
        ('attribs', diff_attribs(font_a, font_b)),
        ('glyphs', diff_glyphs(font_a, font_b)),
        ('names', diff_nametable(font_a, font_b)),
    ]

    for category, diff in diffs:
        for comparison in comparisons:
            if hasattr(diff, comparison):
                d[category][comparison] = getattr(diff, comparison)
    return d


@timer
def diff_nametable(font_a, font_b):
    nametable_a = dump_nametable(font_a)
    nametable_b = dump_nametable(font_b)

    missing = _subtract_names(nametable_a, nametable_b)
    new = _subtract_names(nametable_b, nametable_a)
    modified = _modified_names(nametable_a, nametable_b)

    Names = namedtuple('Names', ['new', 'missing', 'modified'])
    return Names(new, missing, modified)


def _subtract_names(nametable_a, nametable_b):

    names_a_h = {i['id']: i for i in nametable_a}
    names_b_h = {i['id']: i for i in nametable_b}

    missing = set(names_a_h.keys()) - set(names_b_h.keys())

    table = []
    for k in missing:
        table.append(names_a_h[k])
    return table


def _modified_names(nametable_a, nametable_b):

    names_a_h = {i['id']: i for i in nametable_a}
    names_b_h = {i['id']: i for i in nametable_b}

    shared = set(names_a_h.keys()) & set(names_b_h.keys())

    table = []
    for k in shared:
        if names_a_h[k]['string'] != names_b_h[k]['string']:
            row = {
                'id': names_a_h[k]['id'],
                'string_a': names_a_h[k]['string'],
                'string_b': names_b_h[k]['string']
            }
            table.append(row)
    return table


@timer
def diff_glyphs(font_a, font_b):
    # TODO (M FOLEY) work shape diff in here
    glyphs_a = dump_glyphs(font_a)
    glyphs_b = dump_glyphs(font_b)

    missing = _subtract_glyphs(glyphs_a, glyphs_b)
    new = _subtract_glyphs(glyphs_b, glyphs_a)
    modified = _modified_glyphs(glyphs_a, glyphs_b)

    Glyphs = namedtuple('Glyphs', ['new', 'missing', 'modified'])
    return Glyphs(new, missing, modified)


@timer
def diff_kerning(font_a, font_b):
    """Kerns are flattened and then tested for differences."""
    kern_a = dump_kerning(font_a)
    kern_b = dump_kerning(font_b)

    missing = _subtract_kerns(kern_a, kern_b)
    new = _subtract_kerns(kern_b, kern_a)
    modified = _modified_kerns(kern_a, kern_b)

    Kern = namedtuple('KernDiff', ['new', 'missing', 'modified'])
    return Kern(new, missing, modified)


def _subtract_kerns(kern_a, kern_b):

    kern_a_h = {i['left'].kkey + i['right'].kkey: i for i in kern_a}
    kern_b_h = {i['left'].kkey + i['right'].kkey: i for i in kern_b}

    missing_kerns = set(kern_a_h.keys()) - set(kern_b_h.keys())

    table = []
    for k in missing_kerns:
        table.append(kern_a_h[k])

    return sorted(table, key=lambda k: abs(k['value']), reverse=True)


def _modified_kerns(kern_a, kern_b):

    kern_a_h = {i['left'].kkey + i['right'].kkey: i for i in kern_a}
    kern_b_h = {i['left'].kkey + i['right'].kkey: i for i in kern_b}

    shared = set(kern_a_h.keys()) & set(kern_b_h.keys())

    table = []
    for k in shared:
        if kern_a_h[k]['value'] != kern_b_h[k]['value']:
            kern_diff = kern_a_h[k]
            kern_diff['diff'] = kern_b_h[k]['value'] - kern_a_h[k]['value']
            del kern_diff['value']
            table.append(kern_diff)
    return sorted(table, key=lambda k: abs(k['diff']), reverse=True)


@timer
def diff_metrics(font_a, font_b):
    metrics_a = dump_glyph_metrics(font_a)
    metrics_b = dump_glyph_metrics(font_b)

    modified = _modified_metrics(metrics_a, metrics_b)

    Metrics = namedtuple('Metrics', ['modified'])
    return Metrics(modified)


def _modified_metrics(metrics_a, metrics_b):

    metrics_a_h = {i['glyph'].kkey: i for i in metrics_a}
    metrics_b_h = {i['glyph'].kkey: i for i in metrics_b}

    shared = set(metrics_a_h.keys()) & set(metrics_b_h.keys())

    table = []
    for k in shared:
        if metrics_a_h[k]['adv'] != metrics_b_h[k]['adv']:
            metrics = metrics_a_h[k]
            metrics['diff_adv'] = metrics_b_h[k]['adv'] - metrics_a_h[k]['adv']
            metrics['diff_lsb'] = metrics_b_h[k]['lsb'] - metrics_b_h[k]['lsb']
            metrics['diff_rsb'] = metrics_b_h[k]['rsb'] - metrics_b_h[k]['rsb']
            table.append(metrics)
    return sorted(table, key=lambda k: k['diff_adv'], reverse=True)


@timer
def diff_attribs(font_a, font_b):
    attribs_a = dump_attribs(font_a)
    attribs_b = dump_attribs(font_b)

    modified = _modified_attribs(attribs_a, attribs_b)

    Attribs = namedtuple('Attribs', ['modified'])
    return Attribs(modified)


def _modified_attribs(attribs_a, attribs_b):

    attribs_a_h = {i['attrib']: i for i in attribs_a}
    attribs_b_h = {i['attrib']: i for i in attribs_b}

    shared = set(attribs_a_h.keys()) & set(attribs_b_h.keys())

    table = []
    for k in shared:
        if attribs_a_h[k] != attribs_b_h[k]:
            table.append({
                "attrib": attribs_a_h[k]['attrib'],
                "table": attribs_a_h[k]['table'],
                "value_a": attribs_a_h[k]['value'],
                "value_b": attribs_b_h[k]['value']
            })
    return table


def _subtract_glyphs(glyphs_a, glyphs_b):
    glyphs_a_h = {r['glyph'].kkey: r for r in glyphs_a}
    glyphs_b_h = {r['glyph'].kkey: r for r in glyphs_b}

    missing = set(glyphs_a_h.keys()) - set(glyphs_b_h.keys())

    table = []
    for k in missing:
        if glyphs_a_h[k]['glyph'].characters:
            table.append(glyphs_a_h[k])
    return sorted(table, key=lambda k: k['glyph'].name)


def _modified_glyphs(glyphs_a, glyphs_b):
    glyphs_a_h = {r['glyph'].kkey: r for r in glyphs_a}
    glyphs_b_h = {r['glyph'].kkey: r for r in glyphs_b}

    shared = set(glyphs_a_h.keys()) & set(glyphs_b_h.keys())

    table = []
    for k in shared:
        if glyphs_a_h[k]['area'] != glyphs_b_h[k]['area']:
            table.append({
                "glyph": glyphs_a_h[k]['glyph'],
                "diff":  glyphs_b_h[k]['area'] - glyphs_a_h[k]['area']
            })
    return sorted(table, key=lambda k: k['diff'], reverse=True)


@timer
def diff_marks(font_a, font_b):
    """Compare mark positioning differences.

    In order to flatten the class marks, the first mark glyph is chosen for
    marks_a, marks_b will then be flattened using the same mark.

    TODO (M Foley) this approach won't work if marks_b doesn't contain the
    mark chosen in marks_a.
    """
    marks_a = DumpMarks(font_a)
    marks_b = DumpMarks(font_b)

    marks_a = _compress_to_single_mark(marks_a)
    marks_b = _match_marks_in_table(marks_b, marks_a)

    missing = _subtract_marks(marks_a, marks_b)
    new = _subtract_marks(marks_b, marks_a)
    modified = _modified_marks(marks_a, marks_b)

    Marks = namedtuple('Marks', ['new', 'missing', 'modified'])
    return Marks(new, missing, modified)


def _subtract_marks(marks_a, marks_b):

    marks_a_h = {i['base_glyph'].kkey+i['mark_glyph'].kkey: i for i in marks_a}
    marks_b_h = {i['base_glyph'].kkey+i['mark_glyph'].kkey: i for i in marks_b}

    missing = set(marks_a_h.keys()) - set(marks_b_h.keys())

    table = []
    for k in missing:
        table.append(marks_a_h[k])
    return sorted(table, key=lambda k: k['base_glyph'].name)


def _modified_marks(marks_a, marks_b, ignore_thresh=8):

    marks_a_h = {i['base_glyph'].kkey+i['mark_glyph'].kkey: i for i in marks_a}
    marks_b_h = {i['base_glyph'].kkey+i['mark_glyph'].kkey: i for i in marks_b}

    shared = set(marks_a_h.keys()) & set(marks_b_h.keys())

    table = []
    for k in shared:
        offset_a_x = marks_a_h[k]['base_x'] - marks_a_h[k]['mark_x']
        offset_a_y = marks_a_h[k]['base_y'] - marks_a_h[k]['mark_y']
        offset_b_x = marks_b_h[k]['base_x'] - marks_b_h[k]['mark_x']
        offset_b_y = marks_b_h[k]['base_y'] - marks_b_h[k]['mark_y']

        diff_x = offset_a_x != offset_b_x
        diff_y = offset_a_y != offset_b_y

        if diff_x or diff_y:
            mark = marks_a_h[k]
            mark['diff_x'] = offset_b_x - offset_a_x
            mark['diff_y'] = offset_b_y - offset_a_y
            if abs(mark['diff_x']) + abs(mark['diff_y']) < ignore_thresh:
                continue
            for pos in ['base_x', 'base_y', 'mark_x', 'mark_y']:
                mark.pop(pos)
            table.append(mark)

    return sorted(table, key=lambda k: abs(k['diff_x']) + abs(k['diff_y']),
                  reverse=True)


def _compress_to_single_mark(table):
    """table = [
        {'base_glyph': 'x', 'base_x': 0, 'base_y': 0, 'mark_glyphs': [...]}
    ] -->
    table = [
        {'base_glyph': 'x', 'base_x': 0, 'base_y': 0,
         'mark_glyph': 'uni0300', 'mark_x': 0, 'mark_y': 0}
    ]
    """
    new_table = []
    for row in table.base_table:
        row['mark_glyph'] = row['mark_glyphs'][0]['name']
        row['mark_x'] = row['mark_glyphs'][0]['x']
        row['mark_y'] = row['mark_glyphs'][0]['y']
        del row['mark_glyphs']
        new_table.append(row)
    return new_table


def _match_marks_in_table(table, table2):
    """Reduce 'mark_glyphs' list to a single 'mark_glyph' by matching
    the 'mark_glyph' in table2."""
    marks_to_match = set([r['mark_glyph'].kkey for r in table2])

    new_table = []
    for row in table.base_table:
        for idx, mark in enumerate(row['mark_glyphs']):
            if mark['name'].kkey in marks_to_match:
                row['mark_glyph'] = row['mark_glyphs'][idx]['name']
                row['mark_x'] = row['mark_glyphs'][idx]['x']
                row['mark_y'] = row['mark_glyphs'][idx]['y']
                del row['mark_glyphs']
                break
        if 'mark_glyphs' in row.keys():
            del row
        else:
            new_table.append(row)
    return new_table
