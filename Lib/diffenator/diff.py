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
from ttxfont import TTXFont
from metrics import font_glyph_metrics
import shape_diff


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
    20 units is the maximum allowed difference. If a font is monospaced, the
    advanced width should be the same.

    Kerning:
    20 units is the maxium allowed difference

    Mark positioning:
    20 units is the maximum allowed difference

    GSUB:
    No feature should be missing

    """
    d = {}

    font_a = TTXFont(font_a_path)
    font_b = TTXFont(font_b_path)

    kern_a_hash = {(tuple(i.left), tuple(i.right)): i for i in font_a.kern_values}
    kern_b_hash = {(tuple(i.left), tuple(i.right)): i for i in font_b.kern_values}
    d['kerning'] = diff(kern_a_hash, kern_b_hash)

    gsub_a_hash = {(tuple(i.input), tuple(i.result)):i for i in font_a.gsub_rules}
    gsub_b_hash = {(tuple(i.input), tuple(i.result)):i for i in font_b.gsub_rules}
    d['gsub'] = diff(gsub_a_hash, gsub_b_hash, get_modified=False)

    mark_base_a_hash = {(tuple(i.glyph), tuple(i.group)):i for i in font_a.base_anchors}
    mark_base_b_hash = {(tuple(i.glyph), tuple(i.group)):i for i in font_b.base_anchors}
    d['anchors_base'] = diff(mark_base_a_hash, mark_base_b_hash)

    mark_mark_a_hash = {(tuple(i.glyph), tuple(i.group)):i for i in font_a.mark_anchors}
    mark_mark_b_hash = {(tuple(i.glyph), tuple(i.group)):i for i in font_b.mark_anchors}
    d['anchors_mark'] = diff(mark_mark_a_hash, mark_mark_b_hash)

    mark_class_a_hash = {(tuple(i.glyph), tuple(i.group)): i for i in font_a.class_anchors}
    mark_class_b_hash = {(tuple(i.glyph), tuple(i.group)): i for i in font_b.class_anchors}
    d['anchors_class'] = diff(mark_mark_a_hash, mark_mark_b_hash)

    charset_a_hash = {(i): i for i in font_a.getGlyphSet().keys()}
    charset_b_hash = {(i): i for i in font_b.getGlyphSet().keys()}
    d['charset'] = diff(charset_a_hash, charset_b_hash, get_modified=False)

    metrics_a_hash = {(i.glyph): i for i in font_glyph_metrics(font_a)}
    metrics_b_hash = {(i.glyph): i for i in font_glyph_metrics(font_b)}
    d['metrics'] = diff(metrics_a_hash, metrics_b_hash, get_new=False, get_missing=False)

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
    d['charset']['modified'] = [{'glyph': g[0], 'diff': g[1]}
                                for g in shape_report['compared']]
    return d


def diff(coll1, coll2, threshold=20, get_same=False, get_new=True,
         get_missing=True, get_modified=True):
    comp = {}
    if get_missing:
        comp['missing'] = [coll1[i] for i in coll1 if i not in coll2]
    if get_new:
        comp['new'] = [coll2[i] for i in coll2 if i not in coll1]
    if get_same:
        comp['same'] = [coll1[i] for i in coll1 if i in coll2]

    if get_modified:
        shared = set(coll1) & set(coll2)
        modified = []
        for i in shared:
            val1, val2 = coll1[i], coll2[i]
            if val1 != val2:
                try:
                    diff = abs(sum(val1) - sum(val2))
                    if diff > threshold:
                        diff = (val1, val2)
                except TypeError:
                    diff = (val1, val2) 
                modified.append((coll1[i], coll2[i]))
        comp['modified'] = modified
    return comp
