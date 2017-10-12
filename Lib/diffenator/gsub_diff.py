# PR sent for NOTOTOOLS, drop when merged. Keep and improve if not.

# Copyright 2016 Google Inc. All Rights Reserved.
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


"""Provides GsubDiffFinder, which finds differences in GSUB tables.

GsubDiffFinder takes in two paths, to font binaries from which ttxn output is
made. It provides `find_gsub_diffs` which compares the OpenType substitution
rules in these files, reporting the differences via a returned string.
"""
from ttxfont import TTXFont


class GsubDiffFinder(object):
    """Provides methods to report diffs in GSUB content between ttxn outputs."""

    def __init__(self, font_a, font_b, error_bound):
        self._font_a = font_a
        self._font_b = font_b
        self._error_bound = error_bound

        self._new_rules = []
        self._missing_rules = []

    @property
    def new_gsub_rules(self):
        if not self._new_rules:
            self._new_rules = self._subtract_from(
                self._font_b.gsub_rules,
                self._font_a.gsub_rules
            )
        return self._new_rules

    @property
    def missing_gsub_rules(self):
        if not self._missing_rules:
            self._missing_rules = self._subtract_from(
                self._font_a.gsub_rules,
                self._font_b.gsub_rules
            )
        return self._missing_rules

    def _subtract_from(self, coll1, coll2):
        leftover = []
        for item in coll1:
            if item not in coll2:
                leftover.append(item)
        leftover.sort(key=lambda t: t.feature)
        return leftover
