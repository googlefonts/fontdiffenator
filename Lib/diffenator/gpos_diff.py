"""Compare mark positioning and kerning differences"""
from collections import defaultdict
import re
import subprocess
import tempfile
from ttxfont import TTXFont


__all__ = ['MarkDiffFinder', 'KernDiffFinder']


class MarkDiffFinder(object):
    def __init__(self, font_a, font_b, error_bound=20):
        self._font_a = font_a
        self._font_b = font_b
        self._error_bound = error_bound

        self._missing_base_anchors = []
        self._new_base_anchors = []
        self._modified_base_anchors = []

        self._missing_mark_anchors = []
        self._new_mark_anchors = []
        self._modified_mark_anchors = []

        self._missing_mark_classes = []
        self._new_mark_classes = []
        self._modified_mark_classes = []

    @property
    def missing_base_anchors(self):
        if not self._missing_base_anchors:
            self._missing_base_anchors = self._subtract_from(
                self._font_a.base_anchors,
                self._font_b.base_anchors
            )
        return self._missing_base_anchors

    @property
    def new_base_anchors(self):
        if not self._new_base_anchors:
            self._new_base_anchors = self._subtract_from(
                self._font_b.base_anchors,
                self._font_a.base_anchors
            )
        return self._new_base_anchors

    @property
    def modified_base_anchors(self):
        if not self._modified_base_anchors:
            self._modified_base_anchors = self._modified_marks(
                self._font_a.base_anchors,
                self._font_b.base_anchors
            )
        return self._modified_base_anchors

    @property
    def missing_mark_anchors(self):
        if not self._missing_mark_anchors:
            self._missing_mark_anchors = self._subtract_from(
                self._font_a.mark_anchors,
                self._font_b.mark_anchors
            )
        return self._missing_mark_anchors

    @property
    def new_mark_anchors(self):
        if not self._new_mark_anchors:
            self._new_mark_anchors = self._subtract_from(
                self._font_b.mark_anchors,
                self._font_a.mark_anchors
            )
        return self._new_mark_anchors

    @property
    def modified_mark_anchors(self):
        if not self._modified_mark_anchors:
            self._modified_mark_anchors = self._modified_marks(
                self._font_a.mark_anchors,
                self._font_b.mark_anchors
            )
        return self._modified_mark_anchors

    @property
    def missing_mark_classes(self):
        if not self._missing_mark_classes:
            self._missing_mark_classes = self._subtract_from(
                self._font_a.class_anchors,
                self._font_b.class_anchors
            )
        return self._missing_mark_classes

    @property
    def new_mark_classes(self):
        if not self._new_mark_classes:
            self._new_mark_classes = self._subtract_from(
                self._font_b.class_anchors,
                self._font_a.class_anchors
            )
        return self._new_mark_classes

    @property
    def modified_mark_classes(self):
        if not self._modified_mark_classes:
            self._modified_mark_classes = self._modified_marks(
                self._font_a.class_anchors,
                self._font_b.class_anchors
            )
        return self._modified_mark_classes

    def _subtract_from(self, coll1, coll2):
        leftover = []
        known = set(coll2)
        for (glyph, k_class), (val_x, val_y) in coll1.items():
            if (glyph, k_class) not in coll2:
                coord = (val_x, val_y)
                if sum(coord) > self._error_bound:
                    leftover.append({
                        'glyph': glyph,
                        'class': k_class,
                        'coord': coord
                    })
        leftover.sort(key=lambda t: t['glyph'], reverse=True)
        return leftover

    def _modified_marks(self, coll1, coll2):
        modified = []
        shared_keys = [a for a in coll1 if a in coll2]

        for key in shared_keys:
            if coll1[key] != coll2[key]:
                x_diff = coll2[key][0] - coll1[key][0]
                y_diff = coll2[key][1] - coll1[key][1]
                diff = (x_diff, y_diff)
                if sum(diff) > self._error_bound:
                    modified.append({
                        'glyph': key[0],
                        'class': key[1],
                        'coord_diff': (x_diff, y_diff)}
                    )
        modified.sort(key=lambda t: abs(t['coord_diff'][0]) + abs(t['coord_diff'][1]),
                      reverse=True)
        return modified


class KernDiffFinder(object):
    def __init__(self, font_a, font_b, error_bound, font=TTXFont):
        self._font_a = font_a
        self._font_b = font_b
        self._error_bound = error_bound

        self._missing_kerning_values = []
        self._new_kerning_values = []
        self._modified_kerning_values = []

    @property
    def new_kerning_values(self):
        if not self._new_kerning_values:
            self._new_kerning_values = self._subtract_kerns(
                self._font_a.kern_values, self._font_b.kern_values
            )
        return self._new_kerning_values

    @property
    def missing_kerning_values(self):
        if not self._missing_kerning_values:
            self._missing_kerning_values = self._subtract_kerns(
                self._font_b.kern_values, self._font_a.kern_values
            )
        return self._missing_kerning_values

    @property
    def modified_kerning_values(self):
        if not self._modified_kerning_values:
            self._modified_kerning_values = self._find_modified_kerns(
                self._font_a.kern_values, self._font_b.kern_values
            )
        return self._modified_kerning_values

    def _find_modified_kerns(self, kern1, kern2):
        a, b = {}, {}
        modified = []
        for k in kern1:
            a[tuple(k['left']), tuple(k['right'])] = k['value']

        for k in kern2:
            b[tuple(k['left']), tuple(k['right'])] = k['value']

        shared = set(a.keys()) & set(b.keys())

        for pair in shared:
            if a[pair] != b[pair]:
                diff = b[pair] - a[pair]
                if abs(diff) > self._error_bound:
                    modified.append(
                        {'left': list(pair[0]), 
                         'right': list(pair[1]),
                         'kern_diff': diff
                        }
                    )
        modified.sort(key=lambda t: abs(t['kern_diff']), reverse=True)
        return modified

    def _subtract_kerns(self, kern1, kern2):
        leftover = []
        known = [(k['left'], k['right']) for k in kern1]
        for kern in kern2:
            if (kern['left'], kern['right']) not in known:
                if abs(kern['value']) > self._error_bound:
                    leftover.append(kern)
        leftover.sort(key=lambda t: abs(t['value']), reverse=True)
        return leftover
