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

import argparse
import collections
from ttxfont import TTXFont
from fontTools.ttLib import TTFont
from metrics import font_glyph_metrics
from kerning import flatten_kerning
from glyphs import glyph_map
import shape_diff
import attribs


DIFF_THRESH = 1057.5000000000025


def diff_fonts(font_a_path, font_b_path, rendered_diffs=False):
    """
    Compare two fonts against each other.

    Most objects have been derived and improved from Nototools. Hopefully the diff
    objects can be sent back to the nototools upstream upon acceptance of the gf
    engineering team.

    Shapes:
    Half the dot of an 'i' from our collection's thinnest font, Montserrat
    Thin is allowed.

    Metrics:
    20 units is the maximum allowed difference.

    Kerning:
    20 units is the maxium allowed difference

    Mark positioning:
    20 units is the maximum allowed difference

    GSUB:
    No feature should be missing

    """
    d = collections.defaultdict(dict)

    font_a = TTFont(font_a_path)
    font_b = TTFont(font_b_path)

    glyph_map_a = glyph_map(font_a)
    glyph_map_b = glyph_map(font_b)

    kern_a = flatten_kerning(font_a, glyph_map_a)
    kern_b = flatten_kerning(font_b, glyph_map_b)

    d['kern']['missing'] = subtract_kerns(kern_a, kern_b)
    d['kern']['new'] = subtract_kerns(kern_b, kern_a)
    d['kern']['modified'] = modified_kerns(kern_a, kern_b)

    # gsub_a, gsub_b = font_a.gsub_rules, font_b.gsub_rules
    # d['gsub']['new'] = sorted(subtract(gsub_b, gsub_a,['feature', 'input', 'result']),
    #                     key=lambda k: k['feature'])
    # d['gsub']['missing'] = sorted(subtract(gsub_a, gsub_b, ['feature', 'input', 'result']),
    #                     key=lambda k: k['feature'])

    # for anchor_cat in ('base_anchors', 'mark_anchors', 'class_anchors'):
    #     anchors_a = getattr(font_a, anchor_cat)
    #     anchors_b = getattr(font_b, anchor_cat)

    #     d[anchor_cat]['new'] = sorted(subtract(anchors_b, anchors_a, ['glyph', 'group']),
    #                                 key=lambda k: k['glyph'])
    #     d[anchor_cat]['missing'] = sorted(subtract(anchors_a, anchors_b, ['glyph', 'group']),
    #                                     key=lambda k: k['glyph'])
    #     d[anchor_cat]['modified'] = sorted(modified(anchors_a, anchors_b, ['glyph', 'group']),
    #                                     key=lambda k: abs(k['x']) + abs(k['y']))

    # metrics_a = font_glyph_metrics(font_a)
    # metrics_b = font_glyph_metrics(font_b)
    # d['metrics']['modified'] = sorted(modified(metrics_a, metrics_b, ['glyph']),
    #                                     key=lambda k: abs(k['adv']))

    # glyphset_a = [{'glyph': i} for i in font_a.getGlyphSet().keys()]
    # glyphset_b = [{'glyph': i} for i in font_b.getGlyphSet().keys()]
    # d['glyphs']['new'] = sorted(subtract(glyphset_b, glyphset_a),
    #                     key=lambda k: k['glyph'])
    # d['glyphs']['missing'] = sorted(subtract(glyphset_a, glyphset_b),
    #                     key=lambda k: k['glyph'])


    # # Glyph Shaping
    # # TODO (m4rc1e): Rework diff object
    # shape_report = {}
    # shape = shape_diff.ShapeDiffFinder(
    #     font_a_path, font_b_path,
    #     shape_report, diff_threshold=DIFF_THRESH
    # )
    # if rendered_diffs:
    #     shape.find_rendered_diffs()
    # else:
    #     shape.find_area_diffs()
    # shape.cleanup()
    # # print shape_report['compared']
    # d['glyphs']['modified_glyphs'] = sorted(shape_report['compared'],
    #                                 key=lambda k: k[1], reverse=True)

    # table attribs
    attribs_a = attribs.table_attribs(font_a)
    attribs_b = attribs.table_attribs(font_b)
    d['attribs']['modified'] = modified(attribs_a, attribs_b, ['attrib', 'table'])
    return d


def subtract(obj_a, obj_b, keys=None):
    """Compare two lists of dicts and return a list of dicts which are
    in obj_a but not in obj_b.

    Keys are used to find matching dicts between the two lists.

    >>> a = [
            {'glyph': 'a', 'x': 30, 'y': 0},
            {'glyph': 'b', 'x': 0, 'y': 10},
            {'glyph': 'c', 'x': 50, 'y': 0},
    ]

    >>> b = [
            {'glyph': 'a', 'x': 100, 'y': 100},
            {'glyph': 'b', 'x': 0, 'y': 0},
    ]

    >>> subtract(a, b, ['glyph'])
    {'glyph': 'c', 'x': 50, 'y': 0}


    If no keys are given, dictionaries are compared in the similar manner
    as the __eq__ method.

    >>> a[0] == b[0]
    False
    >>> subtract(a, b)
    [
    {'glyph': 'a', 'x': 30, 'y': 0},
    {'glyph': 'c', 'x': 50, 'y': 0},
    ] 

    """
    mod = []
    if keys:
        hash_a = _hash(obj_a, keys)
        hash_b = _hash(obj_b, keys)
    else:
        hash_a = _hash(obj_a, obj_a[0].keys())
        hash_b = _hash(obj_b, obj_b[0].keys())
    return [hash_a[i] for i in hash_a if i not in hash_b]


def modified(obj_a, obj_b, keys):
    """Compare two lists of dicts and return a new list of dicts which
    contain the numerical difference between matching dicts.

    Keys are used to find matching dicts between the two lists.

    a = [
        {'glyph': 'a', 'x': 30, 'y': 0},
        {'glyph': 'b', 'x': 0, 'y': 10},
        {'glyph': 'c', 'x': 50, 'y': 0},
    ]

    b = [
        {'glyph': 'a', 'x': 100, 'y': 100},
        {'glyph': 'b', 'x': 0, 'y': 0},
    ]

    >>> modified(a, b, ['glyph'])
    [{'glyph': 'a': 'x': 70, 'y': 0}]
    """
    mod = []
    hash_a = _hash(obj_a, keys)
    hash_b = _hash(obj_b, keys)

    shared_keys = set(hash_a) & set(hash_b)
    for key in shared_keys:
        if hash_a[key] != hash_b[key]:
            mod.append(_difference_dict(hash_a[key], hash_b[key]))
    return mod


def _hash(obj, keys):
    a = {}
    for item in obj:
        key = _build_prehash(item, keys)
        a[key] = item
    return a


def _build_prehash(obj, keys):
    h = []
    for key in keys:
        if isinstance(obj[key], list):
            key = tuple(obj[key])
            h.append(key)
        else:
            h.append(obj[key])
    return tuple(h)


def _difference_dict(dict_a, dict_b):
    """Get numerical differences between two python dicts

    >>> a = {'a': 100, 'b': 200}
    >>> b = {'a': 30, 'b': 50}
    >>> difference_dict(a, b)
    {'a': 70, 'b': 150}
    """
    d = {}
    for key in dict_a:
        if isinstance(dict_a[key], (int, float)):
            d[key] = dict_b[key] - dict_a[key]
        else:
            d[key] = dict_a[key]
    return d


def subtract_kerns(kern_a, kern_b):

    kern_a_h = {i['left'].kkey + i['right'].kkey: i for i in kern_a}
    kern_b_h = {i['left'].kkey + i['right'].kkey: i for i in kern_b}

    missing_kerns = set(kern_a_h.keys()) - set(kern_b_h.keys())

    table = []
    for k in missing_kerns:
        table.append(kern_a_h[k])

    return sorted(table, key=lambda k: abs(k['value']), reverse=True)


def modified_kerns(kern_a, kern_b):

    kern_a_h = {i['left'].kkey + i['right'].kkey: i for i in kern_a}
    kern_b_h = {i['left'].kkey + i['right'].kkey: i for i in kern_b}

    shared = set(kern_a_h.keys()) & set(kern_b_h.keys())

    table = []
    for k in shared:
        if kern_a_h[k]['value'] != kern_b_h[k]['value']:
            table.append(kern_a_h[k])
    return sorted(table, key=lambda k: abs(k['value']), reverse=True)
