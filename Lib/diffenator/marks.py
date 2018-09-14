import logging

logger = logging.getLogger(__name__)


class DumpMarks:
    """Dump a font's mark and mkmks positions"""
    def __init__(self, font):
        self._font = font
        self._lookups = self._get_lookups() if 'GPOS' in font.keys() else []

        self._base = []
        self._marks = []

        self._mark1 = []
        self._mark2 = []
        self._get_groups()

        self._mark_table = self._gen_table(self._base, self._marks, anc2_is_combining=True)
        self._mkmk_table = self._gen_table(self._mark1, self._mark2,
                                           anc1_is_combining=True,
                                           anc2_is_combining=True)

    @property
    def base_groups(self):
        return self._base

    @property
    def mark_groups(self):
        return self._marks

    @property
    def mark_table(self):
        return self._mark_table

    @property
    def mkmk_table(self):
        return self._mkmk_table

    def _get_lookups(self):
        """Return the lookups used for the mark and mkmk feature"""
        gpos = self._font['GPOS']
        lookups = []
        lookup_idxs = []
        for feat in gpos.table.FeatureList.FeatureRecord:
            if feat.FeatureTag in ['mark', 'mkmk']:
                lookup_idxs += feat.Feature.LookupListIndex

        for idx in lookup_idxs:
            lookups.append(gpos.table.LookupList.Lookup[idx])
        if len(lookups) == 0:
            logger.warn("Font has no mark positioned glyphs")
        return lookups

    def _get_groups(self):
        for lookup in self._lookups:
            for sub_table in lookup.SubTable:

                if hasattr(sub_table, 'ExtSubTable'):
                    sub_table = sub_table.ExtSubTable

                # get mark marks
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

                # get mkmk marks
                if sub_table.Format == 1 and sub_table.LookupType == 6:
                    mark1_lookup_anchors = self._get_mark_anchors(
                        sub_table.Mark1Coverage.glyphs,
                        sub_table.Mark1Array.MarkRecord
                    )
                    mark2_lookup_anchors = self._get_base_anchors(
                        sub_table.Mark2Coverage.glyphs,
                        sub_table.Mark2Array.Mark2Record,
                        anc_type='Mark2Anchor'
                    )
                    self._mark1.append(mark1_lookup_anchors)
                    self._mark2.append(mark2_lookup_anchors)

    def _get_base_anchors(self, glyph_list, anchors_list,
                          anc_type='BaseAnchor'):
        """
        rtype:
        {0: [{'class': 0, 'glyph': 'A', 'x': 199, 'y': 0}],
        {1: [{'class': 0, 'glyph': 'C', 'x': 131, 'y': 74}],
         """
        _anchors = {}
        for glyph, anchors in zip(glyph_list, anchors_list):
            anchors = getattr(anchors, anc_type)
            for idx, anchor in enumerate(anchors):
                if not anchor:  # TODO (M Foley) investigate why fonttools adds Nonetypes
                    continue

                if idx not in _anchors:
                    _anchors[idx] = []
                _anchors[idx].append({
                    'class': idx,
                    'glyph': self._font.input_map[glyph],
                    'x': anchor.XCoordinate,
                    'y': anchor.YCoordinate
                })
        return _anchors

    def _get_mark_anchors(self, glyph_list, anchors_list):
        """
        rtype:
        {0: [{'class': 0, 'glyph': 'uni0300', 'x': 199, 'y': 0}],
        {1: [{'class': 0, 'glyph': 'uni0301', 'x': 131, 'y': 74}],
         """
        _anchors = {}
        for glyph, anchor in zip(glyph_list, anchors_list):
            if not anchor:  # TODO (M Foley) investigate why fonttools adds Nonetypes
                continue

            if anchor.Class not in _anchors:
                _anchors[anchor.Class] = []
            _anchors[anchor.Class].append({
                'glyph': self._font.input_map[glyph],
                'class': anchor.Class,
                'x': anchor.MarkAnchor.XCoordinate,
                'y': anchor.MarkAnchor.YCoordinate
            })
        return _anchors

    def _gen_table(self, anchors1, anchors2,
                   anc1_is_combining=False, anc2_is_combining=False):
        """Return a flattened table consisting of mark1_glyphs with their
        attached mark2_glyphs.

        Returns
        -------
        dump_table: list
        [
            {'mark1_glyph': 'a', 'base_x': 300, 'base_y': 450,
             'mark2_glyph': 'acutecomb', 'mark_x': 0, 'mark_y': 550},
            {'mark1_glyph': 'a', 'base_x': 300, 'base_y': 450,
             'mark2_glyph': 'gravecomb', 'mark_x': 0, 'mark_y': 550},
        ]
        """
        table = []
        for l_idx in range(len(anchors1)):
            for m_group in anchors1[l_idx]:

                for anchor in anchors1[l_idx][m_group]:
                    if anc1_is_combining and not anchor['glyph'].combining:
                        continue
                    for anchor2 in anchors2[l_idx][m_group]:
                        if anc2_is_combining and not anchor2['glyph'].combining:
                            continue
                        table.append({
                            'base_glyph': anchor['glyph'],
                            'base_x': anchor['x'],
                            'base_y': anchor['y'],
                            'mark_glyph': anchor2['glyph'],
                            'mark_x': anchor2['x'],
                            'mark_y': anchor2['y'],
                            'string': anchor['glyph'].characters + anchor2['glyph'].characters,
                            'description': u'{} + {} | {}'.format(
                                anchor['glyph'].name,
                                anchor2['glyph'].name,
                                anchor['glyph'].features
                            ),
                            'features': u'{}, {}'.format(
                                ', '.join(anchor['glyph'].features),
                                ', '.join(anchor2['glyph'].features)
                            )
                        })
        return table
