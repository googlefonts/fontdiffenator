import unittest
from fontTools.ttLib import newTable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._c_m_a_p import cmap_format_4
from fontTools.agl import AGL2UV
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

from diffenator.font import InputFont
from diffenator.attribs import dump_attribs
from diffenator.names import dump_nametable
from diffenator.metrics import dump_glyph_metrics
from diffenator.marks import DumpMarks
from diffenator.kerning import dump_kerning
from diffenator.glyphs import dump_glyphs
from diffenator.diff import (
    _modified_attribs,
    _modified_names,
    _subtract_names,
    _modified_metrics,
    _subtract_glyphs,
    _subtract_marks,
    _modified_marks,
    _compress_to_single_mark,
    _match_marks_in_table,
    _subtract_kerns,
    _modified_kerns
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
            attrs=[('head', 'fontRevision', 1.000)]
        )
        self.font_b = mock_font(
            glyphs=[('a', 400, 50)],
            attrs=[('head', 'fontRevision', 2.000)]
        )

        self.attribs_a = dump_attribs(self.font_a)
        self.attribs_b = dump_attribs(self.font_b)

    def test_diff_attribs(self):
        modified = _modified_attribs(self.attribs_a, self.attribs_b)
        self.assertNotEqual(modified, [])


class TestDiffNames(unittest.TestCase):

    def setUp(self):
        self.font_a = mock_font(
            names=[(unicode("foobar"), 1, 1, 0, 0),
                   (unicode("Regular"), 2, 1, 0, 0)])
        self.font_b = mock_font(
            names=[(unicode("barfoo"), 1, 1, 0, 0)])

        self.names_a = dump_nametable(self.font_a)
        self.names_b = dump_nametable(self.font_b)

    def test_diff_nametable(self):
        modified = _modified_names(self.names_a, self.names_b)
        self.assertNotEqual(modified, [])

    def test_subtract_nametable(self):
        missing = _subtract_names(self.names_a, self.names_b)
        self.assertNotEqual(missing, [])


class TestDiffMetrics(unittest.TestCase):

    def setUp(self):
        self.font_a = mock_font(
            glyphs=[('a', 400, 50)]
        )
        self.font_b = mock_font(
            glyphs=[('a', 550, 10)]
        )
        self.metrics_a = dump_glyph_metrics(self.font_a)
        self.metrics_b = dump_glyph_metrics(self.font_b)

    def test_modified_metrics(self):
        modified = _modified_metrics(self.metrics_a, self.metrics_b)
        self.assertNotEqual(modified, [])


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

        glyphs_a = dump_glyphs(font_a)
        glyphs_b = dump_glyphs(font_b)

        missing = _subtract_glyphs(glyphs_a, glyphs_b)
        self.assertNotEqual(missing, [])

    def test_missing_encoded_glyphs(self):
        font_a = mock_font(glyphs=[('a', 0, 0), ('b', 0, 0)])
        font_b = mock_font(glyphs=[('a', 0, 0)])

        glyphs_a = dump_glyphs(font_a)
        glyphs_b = dump_glyphs(font_b)

        missing_a = _subtract_glyphs(glyphs_a, glyphs_b)
        self.assertNotEqual(missing_a, [])


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

        marks_a = DumpMarks(font_a)
        marks_b = DumpMarks(font_b)

        marks_a = _compress_to_single_mark(marks_a)
        marks_b = _match_marks_in_table(marks_b, marks_a)

        missing = _subtract_marks(marks_a, marks_b)
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
        marks_a = DumpMarks(font_a)
        marks_b = DumpMarks(font_b)

        marks_a = _compress_to_single_mark(marks_a)
        marks_b = _match_marks_in_table(marks_b, marks_a)

        modified = _modified_marks(marks_a, marks_b)
        self.assertNotEqual(modified, [])


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
        kern_a = dump_kerning(font_a)
        kern_b = dump_kerning(font_b)

        missing = _subtract_kerns(kern_a, kern_b)
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
        kern_a = dump_kerning(font_a)
        kern_b = dump_kerning(font_b)

        modified = _modified_kerns(kern_a, kern_b)
        self.assertNotEqual(modified, [])


if __name__ == '__main__':
    unittest.main()
