"""Dump a font's kerning.

TODO (Marc Foley) Flattening produced too much output. Perhaps it's better
to keep the classes and map each class to a single glyph?

Perhaps it would be better to combine our efforts and help improve
https://github.com/adobe-type-tools/kern-dump which has similar
functionality?"""
import logging
logger = logging.getLogger(__name__)

__all__ = ['dump_kerning']


def _kerning_lookup_indexes(font):
    """Return the lookup ids for the kern feature"""
    for feat in font['GPOS'].table.FeatureList.FeatureRecord:
        if feat.FeatureTag == 'kern':
            return feat.Feature.LookupListIndex
    return None


def _flatten_pair_kerning(table, results):
    """Flatten pair on pair kerning"""
    seen = set(results)
    first_glyphs = {idx: g for idx, g in enumerate(table.Coverage.glyphs)}

    for idx, pairset in enumerate(table.PairSet):
        first_glyph = first_glyphs[idx]

        for record in pairset.PairValueRecord:

            kern = (first_glyph, record.SecondGlyph, record.Value1.XAdvance)

            if kern not in seen:
                results.append(kern)
                seen.add(kern)


def _flatten_class_kerning(table, results):
    """Flatten class on class kerning"""
    seen = set(results)
    classes1 = _kern_class(table.ClassDef1.classDefs, table.Coverage.glyphs)
    classes2 = _kern_class(table.ClassDef2.classDefs, table.Coverage.glyphs)

    for idx1, class1 in enumerate(table.Class1Record):
        for idx2, class2 in enumerate(class1.Class2Record):

            if idx1 not in classes1:
                continue
            if idx2 not in classes2:
                continue

            if not hasattr(class2.Value1, 'XAdvance'):
                continue
            if abs(class2.Value1.XAdvance) > 0:
                for glyph1 in classes1[idx1]:
                    for glyph2 in classes2[idx2]:

                        kern = (glyph1, glyph2, class2.Value1.XAdvance)
                        if kern not in seen:
                            results.append(kern)
                            seen.add(kern)


def _kern_class(class_definition, coverage_glyphs):
    """Transpose a ttx classDef

    {glyph_name: idx, glyph_name: idx} --> {idx: [glyph_name, glyph_name]}

    Classdef 0 is not defined in the font. It is created by subtracting
    the glyphs found in the lookup coverage against all the glyphs used to
    define the other classes."""
    classes = {}
    seen_glyphs = set()
    for glyph, idx in class_definition.items():
        if idx not in classes:
            classes[idx] = []
        classes[idx].append(glyph)
        seen_glyphs.add(glyph)

    classes[0] = set(coverage_glyphs) - seen_glyphs
    return classes


def dump_kerning(font):
    """Dump a font's kerning.

    If no GPOS kerns exist, try and dump the kern table instead

    Parameters
    ----------
    font: InputFont

    Returns
    -------
    dump_table: list
        Each row in the table is represented as a dict.
        [
            {'left': A, 'right': V, 'value': -50,
             'string': 'AV', 'description': "AV | ()", 'features': []},
            {'left': V, 'right': A, 'value': -50,
             'string': 'VA', 'description': "VA | ()", 'features': []},
            ...
        ]
    """
    kerning = _dump_gpos_kerning(font)
    if not kerning:
        kerning = _dump_table_kerning(font)
    return kerning


def _dump_gpos_kerning(font):
    if 'GPOS' not in font:
        logger.warning("Font doesn't have GPOS table. No kerns found")
        return []

    kerning_lookup_indexes = _kerning_lookup_indexes(font)
    if not kerning_lookup_indexes:
        logger.warning("Font doesn't have a GPOS kern feature")
        return []

    kern_table = []
    for lookup_idx in kerning_lookup_indexes:
        lookup = font['GPOS'].table.LookupList.Lookup[lookup_idx]

        for sub_table in lookup.SubTable:

            if hasattr(sub_table, 'ExtSubTable'):
                sub_table = sub_table.ExtSubTable

            if hasattr(sub_table, 'PairSet'):
                _flatten_pair_kerning(sub_table, kern_table)

            if hasattr(sub_table, 'ClassDef2'):
                _flatten_class_kerning(sub_table, kern_table)

    kern_table = [{
        'left': font.input_map[left],
        'right': font.input_map[right],
        'value': val,
        'string': font.input_map[left].characters + \
                  font.input_map[right].characters,
        'description': u'{}+{} | {}'.format(
            font.input_map[left].name,
            font.input_map[right].name,
            font.input_map[left].features),
        'features': u'{}, {}'.format(
            ', '.join(font.input_map[left].features),
            ', '.join(font.input_map[right].features)
        )}
        for left, right, val in kern_table]
    return kern_table


def _dump_table_kerning(font):
    """Some fonts still contain kern tables. Most modern fonts include
    kerning in the GPOS table"""
    if not 'kern' in font:
        return []
    logger.warn('Font contains kern table. Newer fonts are GPOS only')
    kerns = []
    for table in font['kern'].kernTables:
        for kern in table.kernTable:
            kerns.append({
                'left': font.input_map[kern[0]],
                'right': font.input_map[kern[1]],
                'value': table.kernTable[kern],
                'string': font.input_map[kern[0]].characters + \
                          font.input_map[kern[1]].characters,
                'description': u'{}+{} | {}'.format(
                    font.input_map[kern[0]].name,
                    font.input_map[kern[1]].name,
                    font.input_map[kern[0]].features),
                'features': u'{}, {}'.format(
                    ', '.join(font.input_map[kern[0]].features),
                    ', '.join(font.input_map[kern[1]].features)
                )
            })
    return kerns
