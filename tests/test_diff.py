import unittest
from fontTools.ttLib import newTable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._c_m_a_p import cmap_format_4
from fontTools.agl import AGL2UV
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

from diffenator.font import InputFont
from diffenator.diff import (
    diff_nametable,
    diff_attribs,
    diff_metrics,
    diff_glyphs,
    diff_marks,
    diff_kerning,
)


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


class TestDiffAttribs(unittest.TestCase):

    def setUp(self):
        self.font_a = mock_font(
            glyphs=[('a', 400, 50)],
            attrs=[('head', 'unitsPerEm', 1000),
                   ('head', 'fontRevision', 1.000)]
        )
        self.font_b = mock_font(
            glyphs=[('a', 400, 50)],
            attrs=[('head', 'unitsPerEm', 1000),
                   ('head', 'fontRevision', 2.000)]
        )

        self.diff = diff_attribs(self.font_a, self.font_b)

    def test_diff_attribs(self):
        modified = self.diff.modified
        self.assertNotEqual(modified, [])

    def test_upm_scale_attribs(self):
        font_a = mock_font(
            attrs=[
                ('head', 'unitsPerEm', 1000),
                ('OS/2', 'sTypoDescender', 700)
            ]
        )
        font_b = mock_font(
            attrs=[('head', 'unitsPerEm', 2000),
                   ('OS/2', 'sTypoDescender', 1400)]
        )
        diff = diff_attribs(font_a, font_b)
        modified = diff.modified
        self.assertEqual(len(modified), 1)

    def test_upm_scale_ignore(self):
        font_a = mock_font(
            attrs=[
                ('head', 'unitsPerEm', 1000),
                ('OS/2', 'fsSelection', 64)
            ]
        )
        font_b = mock_font(
            attrs=[
                ('head', 'unitsPerEm', 2000),
                ('OS/2', 'fsSelection', 128)
            ]
        )
        diff = diff_attribs(font_a, font_b)
        modified = diff.modified
        self.assertNotEqual(modified, [])


class TestDiffNames(unittest.TestCase):

    def setUp(self):
        self.font_a = mock_font(
            names=[(unicode("foobar"), 1, 1, 0, 0),
                   (unicode("Regular"), 2, 1, 0, 0)])
        self.font_b = mock_font(
            names=[(unicode("barfoo"), 1, 1, 0, 0)])

        self.diff = diff_nametable(self.font_a, self.font_b)

    def test_diff_nametable(self):
        modified = self.diff.modified
        self.assertNotEqual(modified, [])

    def test_subtract_nametable(self):
        missing = self.diff.missing
        self.assertNotEqual(missing, [])


class TestDiffMetrics(unittest.TestCase):

    def setUp(self):
        self.font_a = mock_font(
            glyphs=[('a', 400, 50)],
            attrs=[('head', 'unitsPerEm', 1000)]
        )
        self.font_b = mock_font(
            glyphs=[('a', 550, 10)],
            attrs=[('head', 'unitsPerEm', 2048)]
        )
        self.diff = diff_metrics(self.font_a, self.font_b)

    def test_modified_metrics(self):
        modified = self.diff.modified
        self.assertNotEqual(modified, [])

    def test_upm_scale_metrics(self):
        """Check that upm scales are ignored"""
        font_a = mock_font(
            glyphs=[('a', 1134, 0)],
            attrs=[('head', 'unitsPerEm', 1000)]
        )
        font_b = mock_font(
            glyphs=[('a', 2268, 0)],
            attrs=[('head', 'unitsPerEm', 2000)]
        )
        diff = diff_metrics(font_a, font_b,)
        modified = diff.modified
        self.assertEqual(modified, [])


class TestGlyphs(unittest.TestCase):

    def test_ot_glyphs(self):
        font_a = mock_font(
            glyphs=[('a', 100, 100), ('b', 100, 100), ('f.alt', 100, 100)],
            fea='''
            feature liga {
                sub a by f.alt;
            } liga;
        ''')
        font_b = mock_font(
            glyphs=[('a', 100, 100), ('b', 100, 100), ('f.alt', 100, 100)])
        self.diff = diff_glyphs(font_a, font_b)
        missing = self.diff.missing
        self.assertNotEqual(missing, [])

    def test_missing_encoded_glyphs(self):
        font_a = mock_font(glyphs=[('a', 0, 0), ('b', 0, 0)])
        font_b = mock_font(glyphs=[('a', 0, 0)])
        self.diff = diff_glyphs(font_a, font_b)
        missing = self.diff.missing
        self.assertNotEqual(missing, [])


class TestMarks(unittest.TestCase):

    def test_missing_base_mark(self):

        font_a = mock_font(
            glyphs=[('A', 100, 100), ('acutecomb', 0, 0)],
            fea="""
            markClass [acutecomb] <anchor 150 -10> @top;

            feature mark {
                pos base [A]
                 <anchor 85 354> mark @top;
            } mark;
            """
        )
        font_b = mock_font(
            glyphs=[('a', 100, 100)]
        )

        diff = diff_marks(font_a, font_b)
        missing = diff.missing
        self.assertNotEqual(missing, [])

    def test_modified_base_mark(self):
        font_a = mock_font(
            glyphs=[('A', 100, 100), ('acutecomb', 0, 0)],
            fea="""
            markClass [acutecomb] <anchor 150 -10> @top;

            feature mark {
                pos base [A]
                 <anchor 85 354> mark @top;
            } mark;
            """
        )
        font_b = mock_font(
            glyphs=[('A', 100, 100), ('acutecomb', 0, 0)],
            fea="""
            markClass [acutecomb] <anchor 150 -10> @top;

            feature mark {
                pos base [A]
                 <anchor 65 354> mark @top;
            } mark;
            """
        )
        diff = diff_marks(font_a, font_b)
        modified = diff.modified
        self.assertNotEqual(modified, [])

    def test_upm_scale_modified_marks(self):
        font_a = mock_font(
            attrs=[('head', 'unitsPerEm', 1000)],
            glyphs=[('A', 100, 100), ('acutecomb', 0, 0)],
            fea="""
            markClass [acutecomb] <anchor 150 0> @top;

            feature mark {
                pos base [A]
                 <anchor 100 300> mark @top;
            } mark;
            """
        )
        font_b = mock_font(
            attrs=[('head', 'unitsPerEm', 2000)],
            glyphs=[('A', 200, 200), ('acutecomb', 0, 0)],
            fea="""
            markClass [acutecomb] <anchor 300 0> @top;

            feature mark {
                pos base [A]
                 <anchor 200 600> mark @top;
            } mark;
            """
        )
        diff = diff_marks(font_a, font_b)
        modified = diff.modified
        self.assertEqual(modified, [])


class TestKerns(unittest.TestCase):

    def test_missing_kerns(self):
        font_a = mock_font(
            glyphs=[('A', 50, 50), ('V', 50, 50)],
            fea="""
                feature kern {
                pos A V -120;} kern;
            """
        )
        font_b = mock_font(
            glyphs=[('A', 50, 50), ('V', 50, 50)]
        )
        diff = diff_kerning(font_a, font_b)
        missing = diff.missing
        self.assertNotEqual(missing, [])

    def test_modified_kerns(self):
        font_a = mock_font(
            glyphs=[('A', 50, 50), ('V', 50, 50)],
            fea="""
                feature kern {
                pos A V -120;} kern;
            """
        )
        font_b = mock_font(
            glyphs=[('A', 50, 50), ('V', 50, 50)],
            fea="""
                feature kern {
                pos A V -140;} kern;
            """
        )
        diff = diff_kerning(font_a, font_b)
        modified = diff.modified
        self.assertNotEqual(modified, [])

    def test_upm_scale_modified_kerns(self):
        font_a = mock_font(
            attrs=[('head', 'unitsPerEm', 1000)],
            glyphs=[('A', 50, 50), ('V', 50, 50)],
            fea="""
                feature kern {
                pos A V -120;} kern;
            """
        )
        font_b = mock_font(
            attrs=[('head', 'unitsPerEm', 2000)],
            glyphs=[('A', 100, 100), ('V', 100, 100)],
            fea="""
                feature kern {
                pos A V -240;} kern;
            """
        )
        diff = diff_kerning(font_a, font_b)
        modified = diff.modified
        self.assertEqual(modified, [])


if __name__ == '__main__':
    unittest.main()
