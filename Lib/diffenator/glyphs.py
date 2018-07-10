"""Dump a fontfs glyf table"""
from diffenator.font import InputFont
from fontTools.pens.areaPen import AreaPen


def glyph_area(glyphset, glyph):
    """Get the surface area of a glyph"""
    pen = AreaPen(glyphset)
    glyphset[glyph].draw(pen)
    return pen.value


def dump_glyphs(font):
    glyphset = font.getGlyphSet()
    return [{
             'glyph': glyph,
             'area': glyph_area(glyphset, name),
             'string': glyph.characters,
             'description': u'{} | {}'.format(glyph.name, glyph.features),
             'features': u', '.join(glyph.features)}
            for name, glyph in sorted(font.input_map.items())]
