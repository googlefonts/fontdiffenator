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

import collections
from fontTools.ttLib import TTFont
from metrics import dump_glyph_metrics
from kerning import dump_kerning
from attribs import dump_attribs
from names import dump_nametable
from marks import dump_marks
from inputgen import glyph_map
from collections import namedtuple
import shape_diff


__all__ = ['diff_fonts', 'diff_metrics', 'diff_kerning',
           'diff_marks', 'diff_attribs', 'diff_glyphs']


DIFF_THRESH = 1057.5000000000025


def diff_fonts(font_a_path, font_b_path, rendered_diffs=False):
    """Compare two fonts and return the difference for:
    Kerning, Marks, Attributes, Metrics and Input sequences"""
    d = collections.defaultdict(dict)

    font_a = TTFont(font_a_path)
    font_b = TTFont(font_b_path)

    glyph_map_a = glyph_map(font_a)
    glyph_map_b = glyph_map(font_b)

    comparisons = ['new', 'missing', 'modified']
    diffs = [
        ('kern', diff_kerning(font_a, font_b, glyph_map_a, glyph_map_b)),
        ('metrics', diff_metrics(font_a, font_b, glyph_map_a, glyph_map_b)),
        ('marks', diff_marks(font_a, font_b, glyph_map_a, glyph_map_b)),
        ('attribs', diff_attribs(font_a, font_b)),
        ('glyphs', diff_glyphs(glyph_map_a, glyph_map_b)),
        ('names', diff_nametable(font_a, font_b)),
    ]

    for category, diff in diffs:
        for comparison in comparisons:
            if hasattr(diff, comparison):
                d[category][comparison] = getattr(diff, comparison)

    # Glyph Shaping
    # TODO (m4rc1e): Rework diff object
    shape_report = {}
    shape = shape_diff.ShapeDiffFinder(
        font_a_path, font_b_path,
        shape_report, diff_threshold=DIFF_THRESH
    )
    if rendered_diffs:
        shape.find_rendered_diffs()
    else:
        shape.find_area_diffs()
    shape.cleanup()

    return d


def diff_nametable(ttfont_a, ttfont_b):
    nametable_a = dump_nametable(ttfont_a)
    nametable_b = dump_nametable(ttfont_b)

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


def diff_glyphs(glyph_map_a, glyph_map_b):
    # TODO (M FOLEY) work shape diff in here
    glyphset_a = [i for i in glyph_map_a.values()]
    glyphset_b = [i for i in glyph_map_b.values()]

    missing = _subtract_glyphs(glyphset_a, glyphset_b)
    new = _subtract_glyphs(glyphset_b, glyphset_a)

    Glyphs = namedtuple('Glyphs', ['new', 'missing'])
    return Glyphs(new, missing)


def diff_kerning(ttfont_a, ttfont_b, glyph_map_a=None, glyph_map_b=None):

    kern_a = dump_kerning(ttfont_a, glyph_map_a)
    kern_b = dump_kerning(ttfont_b, glyph_map_b)

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
            table.append(kern_diff)
    return sorted(table, key=lambda k: abs(k['diff']), reverse=True)


def diff_metrics(ttfont_a, ttfont_b, glyph_map_a, glyph_map_b):
    metrics_a = dump_glyph_metrics(ttfont_a, glyph_map_a)
    metrics_b = dump_glyph_metrics(ttfont_b, glyph_map_b)

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


def diff_attribs(ttfont_a, ttfont_b):
    attribs_a = dump_attribs(ttfont_a)
    attribs_b = dump_attribs(ttfont_b)

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


def _subtract_glyphs(glyphset_a, glyphset_b):
    glyphset_a_h = {i.kkey: i for i in glyphset_a}
    glyphset_b_h = {i.kkey: i for i in glyphset_b}

    missing = set(glyphset_a_h.keys()) - set(glyphset_b_h.keys())

    table = []
    for k in missing:
        if glyphset_a_h[k].characters:
            table.append({'glyph': glyphset_a_h[k]})
    return sorted(table, key=lambda k: k['glyph'].name)


def diff_marks(ttfont_a, ttfont_b, glyph_map_a, glyph_map_b):
    marks_a = dump_marks(ttfont_a, glyph_map_a)
    marks_b = dump_marks(ttfont_b, glyph_map_b)

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


def _modified_marks(marks_a, marks_b):

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
            for pos in ['base_x', 'base_y', 'mark_x', 'mark_y']:
                mark.pop(pos)
            table.append(mark)
    return sorted(table, key=lambda k: k['base_glyph'].name)
