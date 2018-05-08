from fontTools.ttLib import newTable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._c_m_a_p import cmap_format_4
from fontTools.agl import AGL2UV
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

from diffenator.font import InputFont


def mock_font(names=None,
              attrs=None,
              glyphs=None,
              fea=None):
    """Create a dummy font to test."""
    font = InputFont()
    if names:
        _mock_set_names(font, names)
    if attrs:
        _mock_set_attr(font, attrs)
    else:
        attrs = [('head', 'unitsPerEm', 1000)]
        _mock_set_attr(font, attrs)
    if glyphs:
        _mock_set_glyphs(font, glyphs)
    if fea:
        addOpenTypeFeaturesFromString(font, fea)
    font.recalc_input_map()
    return font


def _mock_set_names(font, names):
    font['name'] = name = newTable('name')
    for entry in names:
        font['name'].setName(*entry)


def _mock_set_attr(font, attrs):
    for table, attr, value in attrs:
        if table not in font.keys():
            font[table] = newTable(table)
        setattr(font[table], attr, value)


def _mock_set_glyphs(font, glyphs):
    font.setGlyphOrder([g[0] for g in glyphs])
    font['hmtx'] = hmtx = newTable('hmtx')
    font['glyf'] = glyf = newTable('glyf')
    font['cmap'] = cmap = newTable('cmap')
    glyph_order = font.getGlyphOrder()
    font['glyf'].glyphs = {}
    font['glyf'].glyphOrder = glyph_order

    for name, adv, rsb in glyphs:
        pen = TTGlyphPen(None)
        font['glyf'][name] = pen.glyph()

    font['hmtx'].metrics = {}
    for name, adv, rsb in glyphs:
        font['hmtx'][name] = (adv, rsb)

    table = cmap_format_4(4)
    table.platformID = 3
    table.platEncID = 1
    table.language = 0
    table.cmap = {AGL2UV[n]: n for n in glyph_order if n in AGL2UV}
    font['cmap'].tableVersion = 0
    font['cmap'].tables = [table]

