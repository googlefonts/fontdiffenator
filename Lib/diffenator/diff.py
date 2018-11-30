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
Module to diff fonts.
"""
from __future__ import print_function
import collections
from diffenator.utils import render_string
from diffenator import DiffTable
import functools
import os
import time
import logging

__all__ = ['DiffFonts', 'diff_metrics', 'diff_kerning',
            'diff_marks', 'diff_mkmks', 'diff_attribs', 'diff_glyphs']

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def timer(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            logger.info('%r  %2.2f ms' % \
                  (method.__name__, (te - ts) * 1000))
        return result
    return timed


class DiffFonts:
    _settings = dict(
        glyphs_thresh=0,
        marks_thresh=0,
        mkmks_thresh=0,
        metrics_thresh=0,
        kerns_thresh=0,
        to_diff=set(["*"]),
    )
    def __init__(self, font_a, font_b, settings=None):
        self._font_a = font_a
        self._font_b = font_b
        self._data = collections.defaultdict(dict)
        if settings:
            for key in settings:
                self._settings[key] = settings[key]

        if {"names", "*"} >= self._settings["to_diff"]:
            self.names()
        if {"attribs", "*"} >= self._settings["to_diff"]:
            self.attribs()
        if {"glyphs", "*"} >= self._settings["to_diff"]:
            self.glyphs(self._settings["glyphs_thresh"])
        if {"kerns", "*"} >= self._settings["to_diff"]:
            self.kerns(self._settings["kerns_thresh"])
        if {"metrics", "*"} >= self._settings["to_diff"]:
            self.metrics(self._settings["metrics_thresh"])
        if {"marks", "*"} >= self._settings["to_diff"]:
            self.marks(self._settings["marks_thresh"])
        if {"mkmks", "*"} >= self._settings["to_diff"]:
            self.mkmks(self._settings["mkmks_thresh"])

    def to_dict(self):
        serialised_data = self._serialise()
        return serialised_data

    def to_gifs(self, dst):
        """output before and after gifs for table"""
        if not os.path.isdir(dst):
            os.mkdir(dst)

        for table in self._data:
            for subtable in self._data[table]:
                _table = self._data[table][subtable]
                if not _table.renderable or len(_table) < 1:
                    continue
                filename = _table.table_name.replace(" ", "_") + ".gif"
                img_path = os.path.join(dst, filename)
                _table.to_gif(img_path)
                

    def to_txt(self, limit=50, dst=None):
        """Output before and after report as .txt doc"""
        report = []
        for table in self._data:
            for subtable in self._data[table]:
                _table = self._data[table][subtable]
                if len(_table) < 1:
                    continue
                report.append(_table.to_txt(limit=limit))
        if dst:
            with open(dst, 'w') as doc:
                doc.write("\n\n".join(report))
        else:
            return "\n\n".join(report)

    def to_md(self, limit=50, dst=None):
        """output before and after report as .md doc"""
        report = []
        for table in self._data:
            for subtable in self._data[table]:
                _table = self._data[table][subtable]
                if len(_table) < 1:
                    continue
                report.append(_table.to_md(limit=limit))
        if dst:
            with open(dst, 'w') as doc:
                doc.write("\n\n".join(report))
        else:
            return "\n\n".join(report)

    def _serialise(self):
        """Serialiser for container data"""
        pass

    def marks(self, threshold=_settings["marks_thresh"]):
        self._data["marks"] = diff_marks(
                self._font_a, self._font_b,
                self._font_a.marks, self._font_b.marks,
                name="marks",
                thresh=threshold
        )

    def mkmks(self, threshold=_settings["mkmks_thresh"]):
        self._data["mkmks"] = diff_marks(
            self._font_a, self._font_b,
            self._font_a.mkmks, self._font_b.mkmks,
            name="mkmks",
            thresh=threshold
        )

    def metrics(self, threshold=_settings["metrics_thresh"]):
        self._data["metrics"] = diff_metrics(self._font_a, self._font_b,
                thresh=threshold)

    def glyphs(self, threshold=_settings["glyphs_thresh"],
               render_diffs=False):
        self._data["glyphs"] = diff_glyphs(self._font_a, self._font_b,
            thresh=threshold, render_diffs=render_diffs)

    def kerns(self, threshold=_settings["kerns_thresh"]):
        self._data["kerns"] = diff_kerning(self._font_a, self._font_b,
            thresh=threshold)

    def attribs(self):
        self._data["attribs"] = diff_attribs(self._font_a, self._font_b)

    def names(self):
        self._data["names"] = diff_nametable(self._font_a, self._font_b)


def _subtract_items(items_a, items_b):
    subtract = set(items_a.keys()) - set(items_b.keys())
    return [items_a[i] for i in subtract]


@timer
def diff_nametable(font_a, font_b):
    """Find nametable differences between two fonts.

    Rows are matched by attribute id.

    Parameters
    ----------
    font_a: DFont
    font_b: DFont

    Returns
    -------
    DiffTable
    """
    nametable_a = font_a.names
    nametable_b = font_b.names

    names_a_h = {i['id']: i for i in nametable_a}
    names_b_h = {i['id']: i for i in nametable_b}

    missing = _subtract_items(names_a_h, names_b_h)
    new = _subtract_items(names_b_h, names_a_h)
    modified = _modified_names(names_a_h, names_b_h)

    new = DiffTable("names new", font_a, font_b, data=new)
    new.report_columns(["id", "string"])
    new.sort(key=lambda k: k["id"])
    missing = DiffTable("names missing", font_a, font_b, data=missing)
    missing.report_columns(["id", "string"])
    missing.sort(key=lambda k: k["id"])
    modified = DiffTable("names modified", font_a, font_b, data=modified)
    modified.report_columns(["id", "string_a", "string_b"])
    modified.sort(key=lambda k: k["id"])
    return {
        'new': new,
        'missing': missing,
        'modified': modified,
    }


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
def diff_glyphs(font_a, font_b, thresh=0.00, scale_upms=True, render_diffs=False):
    """Find glyph differences between two fonts.

    Rows are matched by glyph key, which consists of
    the glyph's characters and OT features.

    Parameters
    ----------
    font_a: DFont
    font_b: DFont
    thresh: Ignore differences below this value
    scale_upms:
        Scale values in relation to the font's upms. See readme
        for example.
    render_diffs: Boolean
        If True, diff glyphs by rendering them. Return ratio of changed
        pixels.
        If False, diff glyphs by calculating the surface area of each glyph.
        Return ratio of changed surface area.

    Returns
    -------
    dict
        {
            "new": DiffTable,
            "missing": DiffTable,
            "modified": DiffTable
        }
    """
    glyphs_a = font_a.glyphs
    glyphs_b = font_b.glyphs

    glyphs_a_h = {r['glyph'].key: r for r in glyphs_a}
    glyphs_b_h = {r['glyph'].key: r for r in glyphs_b}

    missing = _subtract_items(glyphs_a_h, glyphs_b_h)
    new = _subtract_items(glyphs_b_h, glyphs_a_h)
    modified = _modified_glyphs(glyphs_a_h, glyphs_b_h, thresh,
                                scale_upms=scale_upms, render_diffs=render_diffs)
    
    new = DiffTable("glyphs new", font_a, font_b, data=new, renderable=True)
    new.report_columns(["glyph", "area", "string"])
    new.sort(key=lambda k: k["glyph"].name)

    missing = DiffTable("glyphs missing", font_a, font_b, data=missing, renderable=True)
    missing.report_columns(["glyph", "area", "string"])
    missing.sort(key=lambda k: k["glyph"].name)

    modified = DiffTable("glyphs modified", font_a, font_b, data=modified, renderable=True)
    modified.report_columns(["glyph", "diff", "string"])
    modified.sort(key=lambda k: abs(k["diff"]), reverse=True)
    return {
        'new': new,
        'missing': missing,
        'modified': modified
    }


def _modified_glyphs(glyphs_a, glyphs_b, thresh=0.00,
                     upm_a=None, upm_b=None, scale_upms=False, render_diffs=False):
    if render_diffs:
        logger.info('Rendering glyph differences. Be patient')
    shared = set(glyphs_a.keys()) & set(glyphs_b.keys())

    table = []
    for k in shared:
        if scale_upms and upm_a and upm_b:
            glyphs_a[k]['area'] = (glyphs_a[k]['area'] / upm_a) * upm_b
            glyphs_b[k]['area'] = (glyphs_b[k]['area'] / upm_b) * upm_a

        if render_diffs:
            font_a = glyphs_a[k]['glyph'].font
            font_b = glyphs_b[k]['glyph'].font
            glyph = glyphs_a[k]
            diff = diff_rendering(font_a, font_b, glyph['string'], glyph['features'])
        else:
            # using abs does not take into consideration if a curve is reversed
            area_a = abs(glyphs_a[k]['area'])
            area_b = abs(glyphs_b[k]['area'])
            diff = diff_area(area_a, area_b)
        if diff > thresh:
            glyph = glyphs_a[k]
            glyph['diff'] = diff
            table.append(glyph)
    return table


def diff_rendering(font_a, font_b, string, features):
    """Render a string for each font and return the different pixel count
    as a percentage"""
    img_a = render_string(font_a, string, features)
    img_b = render_string(font_b, string, features)
    return _diff_images(img_a, img_b)


def diff_area(area_a, area_b):
    area_a = area_a
    area_b = area_b
    smallest = min([area_a, area_b])
    largest = max([area_a, area_b])
    try:
        diff = abs((float(smallest) / float(largest)) - 1)
    except ZeroDivisionError:
        # for this to happen, both the smallest and largest must be 0. This
        # means the glyph is a whitespace glyph such as a space or uni00A0
        diff = 0
    return diff


def _diff_images(img_a, img_b):
    """Compare two rendered images and return the ratio of changed
    pixels.

    TODO (M FOLEY) Crop images so there are no sidebearings to glyphs"""
    width_a, height_a = img_a.size
    width_b, height_b = img_b.size
    data_a = img_a.getdata()
    data_b = img_b.getdata()

    width, height = max(width_a, width_b), max(height_a, height_b)
    offset_ax = (width - width_a) // 2
    offset_ay = (height - height_a) // 2
    offset_bx = (width - width_b) // 2
    offset_by = (height - height_b) // 2

    diff = 0
    for y in range(height):
        for x in range(width):
            ax, ay = x - offset_ax, y - offset_ay
            bx, by = x - offset_bx, y - offset_by
            if (ax < 0 or bx < 0 or ax >= width_a or bx >= width_b or
                ay < 0 or by < 0 or ay >= height_a or by >= height_b):
                diff += 1
            else:
                if data_a[ax + ay *width_a] != data_b[bx + by * width_b]:
                    diff += 1
    return round(diff / float(width * height), 4)


@timer
def diff_kerning(font_a, font_b, thresh=2, scale_upms=True):
    """Find kerning differences between two fonts.

    Class kerns are flattened and then tested for differences.

    Rows are matched by the left and right glyph keys.

    Some fonts use a kern table instead of gpos kerns, test these
    if no gpos kerns exist. This problem exists in Open Sans v1.

    Parameters
    ----------
    font_a: DFont
    font_b: DFont
    thresh: Ignore differences below this value
    scale_upms:
        Scale values in relation to the font's upms. See readme
        for example.

    Returns
    -------
    dict
        {
            "new": [diff_table],
            "missing": [diff_table],
            "modified": [diff_table]
        }
    """
    kern_a = font_a.kerns
    kern_b = font_b.kerns

    upm_a = font_a._ttfont['head'].unitsPerEm
    upm_b = font_b._ttfont['head'].unitsPerEm

    charset_a = set([font_a.glyph(g).key for g in font_a.glyphset])
    charset_b = set([font_b.glyph(g).key for g in font_b.glyphset])

    kern_a_h = {i['left'].key + i['right'].key: i for i in kern_a
                if i['left'].key in charset_b and i['right'].key in charset_b}
    kern_b_h = {i['left'].key + i['right'].key: i for i in kern_b
                if i['left'].key in charset_b and i['right'].key in charset_a}

    missing = _subtract_items(kern_a_h, kern_b_h)
    missing = [i for i in missing if abs(i["value"]) >= 1]
    new = _subtract_items(kern_b_h, kern_a_h)
    new = [i for i in new if abs(i["value"]) >= 1]
    modified = _modified_kerns(kern_a_h, kern_b_h, thresh,
                               upm_a, upm_b, scale_upms=scale_upms)
    missing = DiffTable("kerns missing", font_a, font_b, data=missing, renderable=True)
    missing.report_columns(["left", "right", "value", "string"])
    missing.sort(key=lambda k: abs(k["value"]), reverse=True)

    new = DiffTable("kerns new", font_a, font_b, data=new, renderable=True)
    new.report_columns(["left", "right", "value", "string"])
    new.sort(key=lambda k: abs(k["value"]), reverse=True)
    
    modified = DiffTable("kerns modified", font_a, font_b, data=modified, renderable=True)
    modified.report_columns(["left", "right", "diff", "string"])
    modified.sort(key=lambda k: abs(k["diff"]), reverse=True)
    return {
        'new': new,
        'missing': missing,
        'modified': modified, 
    }


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
    """Find metrics differences between two fonts.

    Rows are matched by each using glyph key, which consists of
    the glyph's characters and OT features.

    Parameters
    ----------
    font_a: DFont
    font_b: DFont
    thresh:
        Ignore modified metrics under this value
    scale_upms:
        Scale values in relation to the font's upms. See readme
        for example.

    Returns
    -------
    dict
        {
            "new": [diff_table],
            "missing": [diff_table],
            "modified": [diff_table]
        }
    """
    metrics_a = font_a.metrics
    metrics_b = font_b.metrics

    upm_a = font_a._ttfont['head'].unitsPerEm
    upm_b = font_b._ttfont['head'].unitsPerEm

    metrics_a_h = {i['glyph'].key: i for i in metrics_a}
    metrics_b_h = {i['glyph'].key: i for i in metrics_b}

    modified = _modified_metrics(metrics_a_h, metrics_b_h, thresh,
                                 upm_a, upm_b, scale_upms)
    modified = DiffTable("metrics modified", font_a, font_b, data=modified, renderable=True)
    modified.report_columns(["glyph", "diff_adv"])
    modified.sort(key=lambda k: k["diff_adv"], reverse=True)
    return {
            'modified': modified 
    }


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
    """Find attribute differences between two fonts.

    Rows are matched by using attrib.

    Parameters
    ----------
    font_a: DFont
    font_b: DFont
    scale_upms:
        Scale values in relation to the font's upms. See readme
        for example.

    Returns
    -------
    dict
        {
            "modified": [diff_table]
        }
    """
    attribs_a = font_a.attribs
    attribs_b = font_b.attribs

    upm_a = font_a._ttfont['head'].unitsPerEm
    upm_b = font_b._ttfont['head'].unitsPerEm

    attribs_a_h = {i['attrib']: i for i in attribs_a}
    attribs_b_h = {i['attrib']: i for i in attribs_b}

    modified = _modified_attribs(attribs_a_h, attribs_b_h,
                                 upm_a, upm_b, scale_upm=scale_upm)
    modified = DiffTable("attribs modified", font_a, font_b, data=modified)
    modified.report_columns(["table", "attrib", "value_a", "value_b"])
    modified.sort(key=lambda k: k["table"])
    return {'modified': modified}


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


@timer
def diff_marks(font_a, font_b, marks_a, marks_b,
               name=None, thresh=4, scale_upms=True):
    """diff mark positioning.

    Marks are flattened first.

    Rows are matched by each base glyph's + mark glyph's key

    Parameters
    ----------
    font_a: DFont
    font_b: DFont
    marks_a: diff_table
    marks_b: diff_table
    thresh: Ignore differences below this value
    scale_upms:
        Scale values in relation to the font's upms. See readme
        for example.

    Returns
    -------
    dict
        {
            "new": [diff_table],
            "missing": [diff_table],
            "modified": [diff_table]
        }
    """
    upm_a = font_a._ttfont['head'].unitsPerEm
    upm_b = font_b._ttfont['head'].unitsPerEm

    charset_a = set([font_a.glyph(g).key for g in font_a.glyphset])
    charset_b = set([font_b.glyph(g).key for g in font_b.glyphset])

    marks_a_h = {i['base_glyph'].key+i['mark_glyph'].key: i for i in marks_a
                 if i['base_glyph'].key in charset_b and i['mark_glyph'].key in charset_b}
    marks_b_h = {i['base_glyph'].key+i['mark_glyph'].key: i for i in marks_b
                 if i['base_glyph'].key in charset_a and i['mark_glyph'].key in charset_a}

    missing = _subtract_items(marks_a_h, marks_b_h)
    new = _subtract_items(marks_b_h, marks_a_h)
    modified = _modified_marks(marks_a_h, marks_b_h, thresh,
                               upm_a, upm_b, scale_upms=True)

    new = DiffTable(name + "_new", font_a, font_b, data=new, renderable=True)
    new.report_columns(["base_glyph", "base_x", "base_y",
                        "mark_glyph", "mark_x", "mark_y"])
    new.sort(key=lambda k: abs(k["base_x"]) - abs(k["mark_x"]) + \
                           abs(k["base_y"]) - abs(k["mark_y"]))

    missing = DiffTable(name + "_missing", font_a, font_b, data=missing,
                        renderable=True)
    missing.report_columns(["base_glyph", "base_x", "base_y",
                            "mark_glyph", "mark_x", "mark_y"])
    missing.sort(key=lambda k: abs(k["base_x"]) - abs(k["mark_x"]) + \
                               abs(k["base_y"]) - abs(k["mark_y"]))
    modified = DiffTable(name + "_modified", font_a, font_b, data=modified,
                         renderable=True)
    modified.report_columns(["base_glyph", "mark_glyph", "diff_x", "diff_y"])
    modified.sort(key=lambda k: abs(k["diff_x"]) + abs(k["diff_y"]), reverse=True)
    return {
        "new": new,
        "missing": missing,
        "modified": modified,
    }


def _modified_marks(marks_a, marks_b, thresh=4,
                    upm_a=None, upm_b=None, scale_upms=False):

    marks = ['base_x', 'base_y', 'mark_x', 'mark_y']

    shared = set(marks_a.keys()) & set(marks_b.keys())

    table = []
    for k in shared:
        if scale_upms and upm_a and upm_b:
            for mark in marks:
                marks_a[k][mark] = (marks_a[k][mark] / float(upm_a)) * upm_a
                marks_b[k][mark] = (marks_b[k][mark] / float(upm_b)) * upm_a

        offset_a_x = marks_a[k]['base_x'] - marks_a[k]['mark_x']
        offset_a_y = marks_a[k]['base_y'] - marks_a[k]['mark_y']
        offset_b_x = marks_b[k]['base_x'] - marks_b[k]['mark_x']
        offset_b_y = marks_b[k]['base_y'] - marks_b[k]['mark_y']

        diff_x = offset_b_x - offset_a_x
        diff_y = offset_b_y - offset_a_y

        if abs(diff_x) > thresh or abs(diff_y) > thresh:
            mark = marks_a[k]
            mark['diff_x'] = diff_x
            mark['diff_y'] = diff_y
            for pos in ['base_x', 'base_y', 'mark_x', 'mark_y']:
                mark.pop(pos)
            table.append(mark)
    return table

