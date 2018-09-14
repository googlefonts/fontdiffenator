"""Dump a font's glyf table"""
from fontTools.pens.areaPen import AreaPen

__all__ = ['dump_glyphs']


def glyph_area(glyphset, glyph):
    """Get the surface area of a glyph"""
    pen = AreaPen(glyphset)
    glyphset[glyph].draw(pen)
    return pen.value


def dump_glyphs(font):
    """Dump info for each glyph in a font

    Parameters
    ----------
    font: InputFont

    Returns
    -------
    dump_table: list
    Each row in the table is represented as a dict.
        [
            {'glyph': A, 'area': 1000, string': 'A',
             'description': "A | ()", 'features': []},
            {'glyph': B, 'area': 1100, string': 'B',
             'description': "B | ()", 'features': []},
            ...
        ]
    """
    glyphset = font.getGlyphSet()
    return [{
             'glyph': glyph,
             'area': glyph_area(glyphset, name),
             'string': glyph.characters,
             'description': u'{} | {}'.format(glyph.name, glyph.features),
             'features': u', '.join(glyph.features)}
            for name, glyph in sorted(font.input_map.items())]
