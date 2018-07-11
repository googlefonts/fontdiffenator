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

anchors_a_h = {(r["base_x"], r["base_y"]): r for r in table)}

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
from kerning import dump_gpos_kerning, dump_table_kerning
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


def diff_fonts(font_a, font_b):
    """Compare two fonts and return the difference for:
    Kerning, Marks, Attributes, Metrics and Input sequences.

    rtype: collection.defaultdict"""
    d = collections.defaultdict(dict)

    marks_a = DumpMarks(font_a)
    marks_b = DumpMarks(font_b)

    comparisons = ['new', 'missing', 'modified']
    diffs = [
        ('kerns', diff_kerning(font_a, font_b)),
        ('metrics', diff_metrics(font_a, font_b)),
        ('marks', diff_marks(font_a, font_b, marks_a.mark_table, marks_b.mark_table)),
        ('mkmks', diff_marks(font_a, font_b, marks_a.mkmk_table, marks_b.mkmk_table)),
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

    names_a_h = {i['id']: i for i in nametable_a}
    names_b_h = {i['id']: i for i in nametable_b}

    missing = _subtract_items(names_a_h, names_b_h)
    new = _subtract_items(names_b_h, names_a_h)
    modified = _modified_names(names_a_h, names_b_h)

    Names = namedtuple('Names', ['new', 'missing', 'modified'])
    return Names(
        sorted(new, key=lambda k: k['id']),
        sorted(missing, key=lambda k: k['id']),
        sorted(modified, key=lambda k: k['id']),
    )


def _modified_names(names_a, names_b):

    shared = set(names_a.keys()) & set(names_b.keys())

    table = []
    for k in shared:
        if names_a[k]['string'] != names_b[k]['string']:
            row = {
                'id': names_a[k]['id'],
                'string_a': names_a[k]['string'],
                'string_b': names_b[k]['string']
            }
            table.append(row)
    return table


@timer
def diff_glyphs(font_a, font_b, thresh=800, scale_upms=True):
    glyphs_a = dump_glyphs(font_a)
    glyphs_b = dump_glyphs(font_b)

    upm_a = font_a['head'].unitsPerEm
    upm_b = font_b['head'].unitsPerEm

    glyphs_a_h = {r['glyph'].kkey: r for r in glyphs_a}
    glyphs_b_h = {r['glyph'].kkey: r for r in glyphs_b}

    missing = _subtract_items(glyphs_a_h, glyphs_b_h)
    new = _subtract_items(glyphs_b_h, glyphs_a_h)
    modified = _modified_glyphs(glyphs_a_h, glyphs_b_h, thresh,
                                upm_a, upm_b, scale_upms=scale_upms)

    Glyphs = namedtuple('Glyphs', ['new', 'missing', 'modified'])
    return Glyphs(
        sorted(new, key=lambda k: k['glyph'].name),
        sorted(missing, key=lambda k: k['glyph'].name),
        sorted(modified, key=lambda k: k['diff'], reverse=True)
    )


@timer
def diff_kerning(font_a, font_b, thresh=2, scale_upms=True):
    """Kerns are flattened and then tested for differences.

    Some fonts use a kern table instead of gpos kerns, test these
    if no gpos kerns exist. This problem exists in Open Sans v1."""
    kern_a = dump_gpos_kerning(font_a)
    kern_b = dump_gpos_kerning(font_b)

    if not kern_a:
        kern_a = dump_table_kerning(font_a)
    if not kern_b:
        kern_b = dump_table_kerning(font_b)

    upm_a = font_a['head'].unitsPerEm
    upm_b = font_b['head'].unitsPerEm

    charset_a = set([font_a.input_map[g].kkey for g in font_a.input_map])
    charset_b = set([font_b.input_map[g].kkey for g in font_b.input_map])

    kern_a_h = {i['left'].kkey + i['right'].kkey: i for i in kern_a
                if i['left'].kkey in charset_b and i['right'].kkey in charset_b}
    kern_b_h = {i['left'].kkey + i['right'].kkey: i for i in kern_b
                if i['left'].kkey in charset_b and i['right'].kkey in charset_a}

    missing = _subtract_items(kern_a_h, kern_b_h)
    new = _subtract_items(kern_b_h, kern_a_h)
    modified = _modified_kerns(kern_a_h, kern_b_h, thresh,
                               upm_a, upm_b, scale_upms=scale_upms)

    Kern = namedtuple('KernDiff', ['new', 'missing', 'modified'])
    return Kern(
        sorted(new, key=lambda k: k['left'].name),
        sorted(missing, key=lambda k: k['left'].name),
        sorted(modified, key=lambda k: abs(k['diff']), reverse=True)
    )


def _subtract_items(items_a, items_b):
    subtract = set(items_a.keys()) - set(items_b.keys())
    return [items_a[i] for i in subtract]


def _modified_kerns(kern_a, kern_b, thresh=2,
                    upm_a=None, upm_b=None, scale_upms=False):

    shared = set(kern_a.keys()) & set(kern_b.keys())

    table = []
    for k in shared:
        if scale_upms and upm_a and upm_b:
            kern_a[k]['value'] = (kern_a[k]['value'] / float(upm_a)) * upm_a
            kern_b[k]['value'] = (kern_b[k]['value'] / float(upm_b)) * upm_a

        diff = kern_b[k]['value'] - kern_a[k]['value']
        if abs(diff) > thresh:
            kern_diff = kern_a[k]
            kern_diff['diff'] = kern_b[k]['value'] - kern_a[k]['value']
            del kern_diff['value']
            table.append(kern_diff)
    return table


@timer
def diff_metrics(font_a, font_b, thresh=1, scale_upms=True):
    metrics_a = dump_glyph_metrics(font_a)
    metrics_b = dump_glyph_metrics(font_b)

    upm_a = font_a['head'].unitsPerEm
    upm_b = font_b['head'].unitsPerEm

    metrics_a_h = {i['glyph'].kkey: i for i in metrics_a}
    metrics_b_h = {i['glyph'].kkey: i for i in metrics_b}

    modified = _modified_metrics(metrics_a_h, metrics_b_h, thresh,
                                 upm_a, upm_b, scale_upms)

    Metrics = namedtuple('Metrics', ['modified'])
    return Metrics(
        sorted(modified, key=lambda k: k['diff_adv'], reverse=True)
    )


def _modified_metrics(metrics_a, metrics_b, thresh=2,
                      upm_a=None, upm_b=None, scale_upms=False):

    shared = set(metrics_a.keys()) & set(metrics_b.keys())

    table = []
    for k in shared:
        if scale_upms and upm_a and upm_b:
            metrics_a[k]['adv'] = (metrics_a[k]['adv'] / float(upm_a)) * upm_a
            metrics_b[k]['adv'] = (metrics_b[k]['adv'] / float(upm_b)) * upm_a

        diff = abs(metrics_b[k]['adv'] - metrics_a[k]['adv'])
        if diff > thresh:
            metrics = metrics_a[k]
            metrics['diff_adv'] = diff
            metrics['diff_lsb'] = metrics_b[k]['lsb'] - metrics_b[k]['lsb']
            metrics['diff_rsb'] = metrics_b[k]['rsb'] - metrics_b[k]['rsb']
            table.append(metrics)
    return table


@timer
def diff_attribs(font_a, font_b, scale_upm=True):
    attribs_a = dump_attribs(font_a)
    attribs_b = dump_attribs(font_b)

    upm_a = font_a['head'].unitsPerEm
    upm_b = font_b['head'].unitsPerEm

    attribs_a_h = {i['attrib']: i for i in attribs_a}
    attribs_b_h = {i['attrib']: i for i in attribs_b}

    modified = _modified_attribs(attribs_a_h, attribs_b_h,
                                 upm_a, upm_b, scale_upm=scale_upm)

    Attribs = namedtuple('Attribs', ['modified'])
    return Attribs(modified)


def _modified_attribs(attribs_a, attribs_b,
                      upm_a=None, upm_b=None, scale_upm=False):

    shared = set(attribs_a.keys()) & set(attribs_b.keys())

    table = []
    for k in shared:
        if scale_upm and upm_a and upm_b:
            # If a font's upm changes the following attribs are not affected
            keep = (
                'modified',
                'usBreakChar',
                'ulUnicodeRange2',
                'ulUnicodeRange1',
                'tableVersion',
                'usLastCharIndex',
                'ulCodePageRange1',
                'version',
                'usMaxContex',
                'usWidthClass',
                'fsSelection',
                'caretSlopeRise',
                'usMaxContext',
                'fontRevision',
                'yStrikeoutSize',
                'usWeightClass',
                'unitsPerEm'
            )
            if attribs_a[k]['attrib'] not in keep and \
               isinstance(attribs_a[k]['value'], (int, float)):
                attribs_a[k]['value'] = round((attribs_a[k]['value'] / float(upm_a)) * upm_b)
                attribs_b[k]['value'] = round((attribs_b[k]['value'] / float(upm_b)) * upm_b)

        if attribs_a[k]['value'] != attribs_b[k]['value']:
            table.append({
                "attrib": attribs_a[k]['attrib'],
                "table": attribs_a[k]['table'],
                "value_a": attribs_a[k]['value'],
                "value_b": attribs_b[k]['value']
            })
    return table


def _modified_glyphs(glyphs_a, glyphs_b, thresh=1000,
                     upm_a=None, upm_b=None, scale_upms=False):

    shared = set(glyphs_a.keys()) & set(glyphs_b.keys())

    table = []
    for k in shared:
        if scale_upms and upm_a and upm_b:
            glyphs_a[k]['area'] = (glyphs_a[k]['area'] / upm_a) * upm_b
            glyphs_b[k]['area'] = (glyphs_b[k]['area'] / upm_b) * upm_a

        # using abs does not take into consideration if a curve is reversed
        diff = abs(glyphs_b[k]['area']) - abs(glyphs_a[k]['area'])
        if diff > thresh:
            glyph = glyphs_a[k]
            glyph['diff'] = diff
            table.append(glyph)
    return table


@timer
def diff_marks(font_a, font_b, marks_a, marks_b, thresh=2, scale_upms=True):
    """Compare mark positioning differences.

    Marks are flattened
    """
    upm_a = font_a['head'].unitsPerEm
    upm_b = font_b['head'].unitsPerEm

    charset_a = set([font_a.input_map[g].kkey for g in font_a.input_map])
    charset_b = set([font_b.input_map[g].kkey for g in font_b.input_map])

    marks_a_h = {i['mark1_glyph'].kkey+i['mark2_glyph'].kkey: i for i in marks_a
                 if i['mark1_glyph'].kkey in charset_b and i['mark2_glyph'].kkey in charset_b}
    marks_b_h = {i['mark1_glyph'].kkey+i['mark2_glyph'].kkey: i for i in marks_b
                 if i['mark1_glyph'].kkey in charset_a and i['mark2_glyph'].kkey in charset_a}

    missing = _subtract_items(marks_a_h, marks_b_h)
    new = _subtract_items(marks_b_h, marks_a_h)
    modified = _modified_marks(marks_a_h, marks_b_h, thresh,
                               upm_a, upm_b, scale_upms=True)

    Marks = namedtuple('Marks', ['new', 'missing', 'modified'])
    return Marks(
        sorted(new, key=lambda k: k['mark1_glyph'].name),
        sorted(missing, key=lambda k: k['mark1_glyph'].name),
        sorted(modified, key=lambda k: abs(k['diff_x']) + abs(k['diff_y']), reverse=True)
    )


def _modified_marks(marks_a, marks_b, thresh=8,
                    upm_a=None, upm_b=None, scale_upms=False):

    marks = ['mark1_x', 'mark1_y', 'mark2_x', 'mark2_y']

    shared = set(marks_a.keys()) & set(marks_b.keys())

    table = []
    for k in shared:
        if scale_upms and upm_a and upm_b:
            for mark in marks:
                marks_a[k][mark] = (marks_a[k][mark] / float(upm_a)) * upm_a
                marks_b[k][mark] = (marks_b[k][mark] / float(upm_b)) * upm_a

        offset_a_x = marks_a[k]['mark1_x'] - marks_a[k]['mark2_x']
        offset_a_y = marks_a[k]['mark1_y'] - marks_a[k]['mark2_y']
        offset_b_x = marks_b[k]['mark1_x'] - marks_b[k]['mark2_x']
        offset_b_y = marks_b[k]['mark1_y'] - marks_b[k]['mark2_y']

        diff_x = offset_b_x - offset_a_x
        diff_y = offset_b_y - offset_a_y

        if abs(diff_x) + abs(diff_y) > thresh:
            mark = marks_a[k]
            mark['diff_x'] = diff_x
            mark['diff_y'] = diff_y
            for pos in ['mark1_x', 'mark1_y', 'mark2_x', 'mark2_y']:
                mark.pop(pos)
            table.append(mark)
    return table
