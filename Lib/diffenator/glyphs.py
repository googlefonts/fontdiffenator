"""Dump a fontfs glyf table"""
from diffenator.font import InputFont
from fontTools.pens.areaPen import AreaPen


def glyph_area(glyphset, glyph):
    """Get the surface area of a glyph"""
    pen = AreaPen(glyphset)
    glyphset[glyph].draw(pen)
    return pen.value


def dump_glyphs(font):
    table = [r for r in font.input_map.values()]
    glyphset = font.getGlyphSet()

    new_table = []
    while table:
        r = table.pop(0)
        new_r = {'glyph': r, 'area': glyph_area(glyphset, r.name)}
        new_table.append(new_r)
    return new_table
