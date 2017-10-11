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

from ttxfont import TTXFont
import metrics_diff
import shape_diff
import charset_diff
import gpos_diff
import gsub_diff
import argparse


DIFF_THRESH = 1057.5000000000025


def diff_fonts(font_a_path, font_b_path, rendered_diffs=False, error_bound=20):
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
    comparison = {}

    diffs = [
        gpos_diff.KernDiffFinder,
        gpos_diff.MarkDiffFinder,
        gsub_diff.GsubDiffFinder,
        metrics_diff.MetricsDiffFinder,
        charset_diff.CharsetDiffFinder,
    ]
    
    font_a = TTXFont(font_a_path)
    font_b = TTXFont(font_b_path)

    for diff in diffs:
        d = diff(font_a, font_b, error_bound=20)
        # Get all @property attribs from comparison objects
        attribs = [a for a in dir(diff)
                   if isinstance(getattr(diff, a), property)]
        for attrib in attribs:
            comparison[attrib] = getattr(d, attrib)

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
    comparison['modified_glyphs'] = [{'glyph': g[0], 'diff': g[1]}
                                    for g in shape_report['compared']]
    return comparison
