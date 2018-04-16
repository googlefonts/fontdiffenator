"""Dump a font's mark and mkmk feature

TODO (M FOLEY) add mkmk feature"""


class DumpMarks:
    def __init__(self, font):
        self._font = font
        self._lookups = self._get_lookups()
        self._base = []
        self._base_anchors = []
        self._mark_anchors = []
        self._marks = []
        self._get_groups()
        self._base_table = self._gen_base_table()
        self._mark_table = self._gen_mark_table()

    @property
    def base_groups(self):
        return self._base

    @property
    def mark_groups(self):
        return self._marks

    @property
    def base_table(self):
        return self._base_table

    @property
    def mark_table(self):
        return self._mark_table

    def flatten_groups(self):
        pass

    @property
    def base_anchors(self):
        if not self._base_anchors:
            self._base_anchors = self._ungroup_anchors(self._base)
        return self._base_anchors

    @property
    def mark_anchors(self):
        if not self._mark_anchors:
            self._mark_anchors = self._ungroup_anchors(self._marks)
        return self._mark_anchors

    def _ungroup_anchors(self, anchors_group):
        anchors = []
        for lookup in anchors_group:
            for idx in lookup:
                anchors += lookup[idx]
        return anchors

    def _get_lookups(self):
        """Return the lookups used for the mark feature"""
        gpos = self._font['GPOS']
        for feat in gpos.table.FeatureList.FeatureRecord:
            if feat.FeatureTag == 'mark':
                lookup_idxs = feat.Feature.LookupListIndex
        lookups = []
        for idx in lookup_idxs:
            lookups.append(gpos.table.LookupList.Lookup[idx])
        return lookups

    def _get_groups(self):
        for lookup in self._lookups:
            for sub_table in lookup.SubTable:
                if sub_table.Format == 1 and sub_table.LookupType == 4:
                    base_lookup_anchors = self._get_base_anchors(
                        sub_table.BaseCoverage.glyphs,
                        sub_table.BaseArray.BaseRecord,
                    )
                    mark_lookup_anchors = self._get_mark_anchors(
                        sub_table.MarkCoverage.glyphs,
                        sub_table.MarkArray.MarkRecord
                    )
                    self._base.append(base_lookup_anchors)
                    self._marks.append(mark_lookup_anchors)

    def _get_base_anchors(self, glyph_list, anchors_list):
        """...
         """
        _anchors = {}
        for glyph, anchors in zip(glyph_list, anchors_list):
            for idx, anchor in enumerate(anchors.BaseAnchor):
                if idx not in _anchors:
                    _anchors[idx] = []
                _anchors[idx].append({
                    'class': idx,
                    'name': glyph,
                    'x': anchor.XCoordinate,
                    'y': anchor.YCoordinate
                })
        return _anchors

    def _get_mark_anchors(self, glyph_list, anchors_list):
        """
        Collect all mark anchors. Store in dict, key is anchor id

        rtype:
        {0: [{'class': 0, 'glyph': 'uni0300', 'x': 199, 'y': 0}],
        {1: [{'class': 0, 'glyph': 'uni0301', 'x': 131, 'y': 74}],
         """
        _anchors = {}
        for glyph, anchor in zip(glyph_list, anchors_list):
            if anchor.Class not in _anchors:
                _anchors[anchor.Class] = []
            _anchors[anchor.Class].append({
                'name': glyph,
                'class': anchor.Class,
                'x': anchor.MarkAnchor.XCoordinate,
                'y': anchor.MarkAnchor.YCoordinate
            })
        return _anchors

    def _gen_base_table(self):
        """Return a table of mark positioned base glyphs. By default, the
        table is not flattened. Only the first mark in each class is
        returned. This keeps the output more human readable"""
        table = []
        for l_idx in range(len(self._base)):
            for m_group in self._base[l_idx]:
                for glyph in self._base[l_idx][m_group]:
                    table.append({
                        'base_glyph': glyph['name'],
                        'base_x': glyph['x'],
                        'base_y': glyph['y'],
                        'mark_glyph': self._marks[l_idx][m_group][0]['name'],
                        'mark_x': self._marks[l_idx][m_group][0]['x'],
                        'mark_y': self._marks[l_idx][m_group][0]['y'],
                    })
        return table

    def _gen_mark_table(self):
        """Return a table of mark positioned base glyphs. By default, the
        table is not flattened. Only the first mark in each class is
        returned. This keeps the output far more human readable"""
        table = []
        seen = set()
        for l_idx in range(len(self._marks)):
            for m_group in self._marks[l_idx]:
                for glyph in self._marks[l_idx][m_group]:
                    if glyph['name'] not in seen:
                        seen.add(glyph['name'])
                        table.append({
                            'mark_glyph': glyph['name'],
                            'mark_x': glyph['x'],
                            'mark_y': glyph['y'],
                            'base_glyph': self._base[l_idx][m_group][0]['name'],
                            'base_x': self._base[l_idx][m_group][0]['x'],
                            'base_y': self._base[l_idx][m_group][0]['y'],
                        })
        return table
