"""Functions to produce font metrics.

Caveat, the rsb implementation is only accurate when curve points are
on the extrema"""

__all__ = ['dump_glyph_metrics']


def glyph_metrics(font, glyph):
    lsb = _glyph_lsb(font, glyph)
    rsb = _glyph_rsb(font, glyph)
    adv = _glyph_adv_width(font, glyph)
    return {'glyph': font.input_map[glyph],
            'lsb': lsb, 'rsb': rsb, 'adv': adv,
            'string': font.input_map[glyph].characters,
            'description': u'{} | {}'.format(
                font.input_map[glyph].name,
                font.input_map[glyph].features
            ),
            'features': u', '.join(font.input_map[glyph].features)}


def dump_glyph_metrics(font):
    """Dump the metrics for each glyph in a font

    Parameters
    ----------
    font: InputFont

    Returns
    -------
    dump_table: list
    Each row in the table is represented as a dict.
        [
            {'glyph': A, 'lsb': 50, 'rsb': 50, 'adv': 200,
             'string': 'A', 'description': "A | ()"},
            {'glyph': B, 'lsb': 80, 'rsb': 50, 'adv': 230,
             'string': 'B', 'description': "B | ()"},
            ...
        ]
    """
    glyphs = font.getGlyphSet().keys()
    return [glyph_metrics(font, g) for g in glyphs]


def _glyph_adv_width(font, glyph):
    return font['hmtx'][glyph][0]


def _glyph_lsb(font, glyph):
    """Get the left side bearing for a glyph.
    If the Xmin attribute does not exist, the font is zero width so
    return 0"""
    try:
        return font['glyf'][glyph].xMin
    except AttributeError:
        return 0


def _glyph_rsb(font, glyph):
    """Get the right side bearing for a glyph.
    If the Xmax attribute does not exist, the font is zero width so
    return 0"""
    glyph_width = font['hmtx'].metrics[glyph][0]
    try:
        return glyph_width - font['glyf'][glyph].xMax
    except AttributeError:
        return 0
