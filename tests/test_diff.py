import unittest
from mockfont import mock_font
from diffenator.marks import DumpMarks
from diffenator.diff import (
    diff_nametable,
    diff_attribs,
    diff_metrics,
    diff_glyphs,
    diff_marks,
    diff_kerning,
    diff_area,
    _diff_images
)
import sys
from PIL import Image
if sys.version_info.major == 3:
    unicode = str


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
        modified = self.diff['modified']
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
        modified = diff['modified']
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
        modified = diff['modified']
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
        modified = self.diff['modified']
        self.assertNotEqual(modified, [])

    def test_subtract_nametable(self):
        missing = self.diff['missing']
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
        modified = self.diff['modified']
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
        modified = diff['modified']
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
        missing = self.diff['missing']
        self.assertNotEqual(missing, [])

    def test_missing_encoded_glyphs(self):
        font_a = mock_font(glyphs=[('a', 0, 0), ('b', 0, 0)])
        font_b = mock_font(glyphs=[('a', 0, 0)])
        self.diff = diff_glyphs(font_a, font_b)
        missing = self.diff['missing']
        self.assertNotEqual(missing, [])

    def test_area(self):
        area_a = 100
        area_b = 75
        self.assertEqual(diff_area(area_a, area_b), 0.25)
        self.assertEqual(diff_area(area_b, area_a), 0.25)

    def test_render_diff_r01(self):
        """Compare a crude F against a blank glyph.

        Half the pixels have changed"""
        img_a_px = [
            255, 1, 1,   1,
            255, 1, 255, 255,
            255, 1, 1,   1,
            255, 1, 255, 255,
        ]
        img_b_px = [
            255, 255, 255, 255,
            255, 255, 255, 255,
            255, 255, 255, 255,
            255, 255, 255, 255,
        ]

        img_a = Image.new('L', (4, 4))
        img_a.putdata(img_a_px)
        img_b = Image.new('L', (4, 4))
        img_b.putdata(img_b_px)
        self.assertEqual(_diff_images(img_a, img_b), 0.5)

    def test_render_diff_r02(self):
        """Glyphs are identical"""
        img_a_px = [
            255, 1, 1,   1,
            255, 1, 255, 255,
            255, 1, 1,   1,
            255, 1, 255, 255,
        ]
        img_b_px = img_a_px
        img_a = Image.new('L', (4, 4))
        img_a.putdata(img_a_px)
        img_b = Image.new('L', (4, 4))
        img_b.putdata(img_b_px)
        self.assertEqual(_diff_images(img_a, img_b), 0.0)

    def test_render_diff_r03(self):
        """Glyphs are offset.

        TODO (M FOLEY) this should return a match.
        The glyphs haven't changed, just the metrics"""
        img_a_px = [
            0  , 0  , 255, 255,
            0  , 0  , 255, 255,
            255, 255, 255, 255,
            255, 255, 255, 255,
        ]
        img_b_px = [
            255, 255, 255, 255,
            255, 0  , 0, 255,
            255, 0  , 0, 255,
            255, 255, 255, 255,
        ]
        img_a = Image.new('L', (4, 4))
        img_a.putdata(img_a_px)
        img_b = Image.new('L', (4, 4))
        img_b.putdata(img_b_px)
        self.assertEqual(_diff_images(img_a, img_b), 0.375)


class TestMarks(unittest.TestCase):

    def test_missing_base_mark(self):

        font_a = mock_font(
            glyphs=[('A', 100, 100), ('acutecomb', 0, 0),
                    ('O', 100, 100)],
            fea="""
            markClass [acutecomb] <anchor 150 -10> @top;

            feature mark {
                pos base [A O]
                 <anchor 85 354> mark @top;
            } mark;
            """
        )
        font_b = mock_font(
            glyphs=[('A', 100, 100), ('acutecomb', 0, 0)]
        )
        marks_a = DumpMarks(font_a)
        marks_b = DumpMarks(font_b)

        diff = diff_marks(font_a, font_b, marks_a.mark_table, marks_b.mark_table)
        missing = diff['missing']
        self.assertNotEqual(missing, [])
        # Diffenator will only return missing and new marks betweeen
        # matching glyph sets. If font_b is missing many glyphs which
        # have marks in font_a, these won't be reported. If the user
        # add the glyphs to font_b without the marks, then it will
        # get reported.
        self.assertEqual(len(missing), 1)

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

        diff = diff_marks(font_a, font_b, marks_a.mark_table, marks_b.mark_table)
        modified = diff['modified']
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
        marks_a = DumpMarks(font_a)
        marks_b = DumpMarks(font_b)

        diff = diff_marks(font_a, font_b, marks_a.mark_table, marks_b.mark_table)
        modified = diff['modified']
        self.assertEqual(modified, [])


class TestMkMks(unittest.TestCase):

    def test_missing_mkmks(self):
        font_a = mock_font(
            glyphs=[('acutecomb', 0, 0), ('gravecomb', 0, 0)],
            fea="""
            markClass [acutecomb gravecomb] <anchor 150 -10> @top;

            feature mark {
                pos mark @top
                 <anchor 85 354> mark @top;
            } mark;
            """
        )
        font_b = mock_font(
            glyphs=[('acutecomb', 0, 0)]
        )
        marks_a = DumpMarks(font_a)
        marks_b = DumpMarks(font_b)

        diff = diff_marks(font_a, font_b, marks_a.mkmk_table, marks_b.mkmk_table)
        missing = diff['missing']
        self.assertNotEqual(missing, [])

    def test_modified_mkmks(self):
        font_a = mock_font(
            glyphs=[('acutecomb', 0, 0), ('gravecomb', 0, 0)],
            fea="""
            markClass [acutecomb gravecomb] <anchor 150 -10> @top;

            feature mark {
                pos mark @top
                 <anchor 85 354> mark @top;
            } mark;
            """
        )
        font_b = mock_font(
            glyphs=[('acutecomb', 0, 0), ('gravecomb', 0, 0)],
            fea="""
            markClass [acutecomb gravecomb] <anchor 0 -10> @top;

            feature mark {
                pos mark @top
                 <anchor 85 354> mark @top;
            } mark;
            """
        )
        marks_a = DumpMarks(font_a)
        marks_b = DumpMarks(font_b)

        diff = diff_marks(font_a, font_b, marks_a.mkmk_table, marks_b.mkmk_table)
        modified = diff['modified']
        self.assertNotEqual(modified, [])
        self.assertEqual(len(modified), 4)


class TestKerns(unittest.TestCase):

    def test_missing_kerns(self):
        font_a = mock_font(
            glyphs=[('A', 50, 50), ('V', 50, 50), ('Y', 50, 50)],
            fea="""
                feature kern {
                pos A V -120;
                pos Y A -120;} kern;
            """
        )
        font_b = mock_font(
            glyphs=[('A', 50, 50), ('V', 50, 50)]
        )
        diff = diff_kerning(font_a, font_b)
        missing = diff['missing']
        self.assertNotEqual(missing, [])
        # Missing and new kerns are only reported for matching glyphs
        # this is the same approach as the missing and new marks diff
        self.assertEqual(len(missing), 1)

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
        modified = diff['modified']
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
        modified = diff['modified']
        self.assertEqual(modified, [])


if __name__ == '__main__':
    unittest.main()
