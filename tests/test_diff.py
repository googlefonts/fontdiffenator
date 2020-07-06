from copy import copy
import unittest
from mockfont import mock_font, test_glyph
from diffenator.diff import (
    DiffFonts,
    diff_nametable,
    diff_attribs,
    diff_metrics,
    diff_glyphs,
    diff_marks,
    diff_kerning,
    diff_area,
    _diff_images,
    diff_gdef_base,
    diff_gdef_mark,
)
import sys
from PIL import Image
if sys.version_info.major == 3:
    unicode = str


class TestDiffAttribs(unittest.TestCase):
 
    def test_diff_attribs(self):
        font_a = mock_font()
        font_a.builder.setupOS2(sTypoAscender=800)
        font_a.recalc_tables()

        font_b = mock_font()
        font_b.builder.setupOS2(sTypoAscender=1000)
        font_b.recalc_tables()

        diff = diff_attribs(font_a, font_b)
        modified = diff['modified']._data
        self.assertNotEqual(modified, [])
        self.assertEqual(len(modified), 1)


    def test_diff_attribs_scale(self):
        font_a = mock_font()
        font_a.builder.setupHead(unitsPerEm=1000)
        font_a.builder.setupOS2(sTypoAscender=1000)
        font_a.recalc_tables()
        font_b = mock_font()
        font_b.builder.setupHead(unitsPerEm=2000)
        font_b.builder.setupOS2(sTypoAscender=2000)
        font_b.recalc_tables()
        diff = diff_attribs(font_a, font_b)
        modified = diff['modified']._data
        self.assertEqual(len(modified), 1) # Only upm should be reported

    def test_upm_scale_ignore(self):
        font_a = mock_font()
        font_a.builder.setupHead(unitsPerEm=1000)
        font_a.builder.setupOS2(fsSelection=32)
        font_a.recalc_tables()
        font_b = mock_font()
        font_b.builder.setupHead(unitsPerEm=2000)
        font_b.builder.setupOS2(fsSelection=32)
        font_b.recalc_tables()
        diff = diff_attribs(font_a, font_b)
        modified = diff['modified']._data
        self.assertEqual(len(modified), 1) # only upm is returned


class TestDiffNames(unittest.TestCase):

    def test_diff_nametable(self):
        font_a = mock_font()
        font_b = mock_font()
        font_a.builder.setupNameTable({"psName": "foobar"})
        font_a.recalc_tables()
        font_b.builder.setupNameTable({"psName": "barfoo"})
        font_b.recalc_tables()
        diff = diff_nametable(font_a, font_b)
        modified = diff['modified']._data
        self.assertNotEqual(modified, [])

    def test_subtract_nametable(self):
        font_a = mock_font()
        font_a.builder.setupNameTable({})
        font_b = mock_font()
        font_a.builder.setupNameTable({"psName": "foobar"})
        font_a.recalc_tables()
        font_b.recalc_tables()
        diff = diff_nametable(font_a, font_b)
        missing = diff["new"]._data
        self.assertNotEqual(missing, [])


class TestDiffMetrics(unittest.TestCase):

    def test_modified_metrics(self):
        font_a = mock_font()
        font_b = mock_font()

        adv_a = {".notdef": 600, "A": 600, "Aacute": 600, "V": 600, ".null": 600, "acutecomb": 0, "gravecomb": 0, "A.alt": 600}
        metrics_a = {}
        glyph_tbl_a = font_a.ttfont["glyf"]
        for gn, adv in adv_a.items():
            metrics_a[gn] = (adv, glyph_tbl_a[gn].xMin)

        adv_b = {".notdef": 600, "A": 500, "Aacute": 600, "V": 600, ".null": 600, "acutecomb": 0, "gravecomb": 0, "A.alt": 600}
        metrics_b = {}
        glyph_tbl_b = font_b.ttfont["glyf"]
        for gn, adv in adv_b.items():
            metrics_b[gn] = (adv, glyph_tbl_b[gn].xMin)
        font_a.builder.setupHorizontalMetrics(metrics_a)
        font_a.recalc_tables()
        font_b.builder.setupHorizontalMetrics(metrics_b)
        font_b.recalc_tables()
        diff = diff_metrics(font_a, font_b)
        modified = diff["modified"]._data
        self.assertNotEqual(modified, [])

    def test_upm_scale_metrics(self):
        """Check that upm scales are ignored"""
        font_a = mock_font()
        font_a.builder.updateHead(unitsPerEm=2000, created=0, modified=0)
        font_a.recalc_tables()
        font_b = mock_font()

        adv_a = {".notdef": 1200, "A": 800, "Aacute": 1200, "V": 1200, ".null": 1200, "acutecomb": 0, "gravecomb": 0, "A.alt": 1200}
        metrics_a = {}
        glyph_tbl_a = font_a.ttfont["glyf"]
        for gn, adv in adv_a.items():
            metrics_a[gn] = (adv, glyph_tbl_a[gn].xMin)

        adv_b = {".notdef": 600, "A": 600, "Aacute": 600, "V": 600, ".null": 600, "acutecomb": 0, "gravecomb": 0, "A.alt": 600}
        metrics_b = {}
        glyph_tbl_b = font_b.ttfont["glyf"]
        for gn, adv in adv_b.items():
            metrics_b[gn] = (adv, glyph_tbl_b[gn].xMin)
        font_a.builder.setupHorizontalMetrics(metrics_a)
        font_a.recalc_tables()
        font_b.builder.setupHorizontalMetrics(metrics_b)
        font_b.recalc_tables()
        diff = diff_metrics(font_a, font_b)
        modified = diff["modified"]._data
        self.assertEqual(len(modified), 1)


class TestGlyphs(unittest.TestCase):

    def test_ot_glyphs(self):
        font_a = mock_font()
        fea="""
                feature salt {
                sub A by A.alt;} salt;
            """
        font_a.builder.addOpenTypeFeatures(fea)
        font_a.recalc_tables()

        font_b = mock_font()
        font_b.recalc_tables()

        self.diff = diff_glyphs(font_a, font_b)
        new = self.diff['missing']._data
        self.assertNotEqual(new, [])

    def test_missing_encoded_glyphs(self):
        font_a = mock_font()

        font_b = mock_font()
        font_b.builder.setupGlyphOrder([".notdef", ".null", "A"])
        font_b.builder.setupCharacterMap({65: "A"})
        glyphs_b = {".notdef": test_glyph(), ".null": test_glyph(), "A": test_glyph()}
        font_b.builder.setupGlyf(glyphs_b)
        font_b.recalc_tables()

        self.diff = diff_glyphs(font_a, font_b)
        missing = self.diff['missing']._data
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

        font_a = mock_font()
        fea="""
            markClass [acutecomb] <anchor 150 -10> @top;

            feature mark {
                pos base [A V]
                 <anchor 85 354> mark @top;
            } mark;
            """
        font_a.builder.addOpenTypeFeatures(fea)
        font_a.recalc_tables()

        font_b = mock_font()
        diff = diff_marks(font_a, font_b, font_a.marks, font_b.marks, 'marks')
        missing = diff['missing']._data
        self.assertNotEqual(missing, [])
        # Diffenator will only return missing and new marks betweeen
        # matching glyph sets. If font_b is missing many glyphs which
        # have marks in font_a, these won't be reported. If the user
        # add the glyphs to font_b without the marks, then it will
        # get reported.
        self.assertEqual(len(missing), 2)

    def test_modified_base_mark(self):
        font_a = mock_font()
        fea="""
            markClass [acutecomb] <anchor 150 -10> @top;

            feature mark {
                pos base [A]
                 <anchor 85 354> mark @top;
            } mark;
            """
        font_a.builder.addOpenTypeFeatures(fea)
        font_a.recalc_tables()
        font_b = mock_font()
        fea="""
            markClass [acutecomb] <anchor 150 -10> @top;

            feature mark {
                pos base [A]
                 <anchor 65 354> mark @top;
            } mark;
            """
        font_b.builder.addOpenTypeFeatures(fea)
        font_b.recalc_tables()
        diff = diff_marks(font_a, font_b, font_a.marks, font_b.marks, "marks")
        modified = diff['modified']._data
        self.assertNotEqual(modified, [])

    def test_upm_scale_modified_marks(self):
        font_a = mock_font()
        font_a.builder.updateHead(unitsPerEm=1000)
        fea="""
            markClass [acutecomb] <anchor 150 0> @top;

            feature mark {
                pos base [A]
                 <anchor 100 300> mark @top;
            } mark;
            """
        font_a.builder.addOpenTypeFeatures(fea)
        font_a.recalc_tables()
        font_b = mock_font()
        font_b.builder.updateHead(unitsPerEm=2000)
        fea="""
            markClass [acutecomb] <anchor 300 0> @top;

            feature mark {
                pos base [A]
                 <anchor 200 600> mark @top;
            } mark;
            """
        font_b.builder.addOpenTypeFeatures(fea)
        font_b.recalc_tables()
        diff = diff_marks(font_a, font_b, font_a.marks, font_b.marks, "marks")
        modified = diff['modified']._data
        self.assertEqual(modified, [])


class TestMkMks(unittest.TestCase):

    def test_missing_mkmks(self):
        font_a = mock_font()
        fea="""
            markClass [acutecomb gravecomb] <anchor 150 -10> @top;

            feature mkmk {
                pos mark @top
                 <anchor 85 354> mark @top;
            } mkmk;
            """
        font_a.builder.addOpenTypeFeatures(fea)
        font_a.recalc_tables()
        font_b = mock_font()

        diff = diff_marks(font_a, font_b, font_a.mkmks, font_b.mkmks, 'mkmks')
        missing = diff['missing']._data
        self.assertNotEqual(missing, [])

    def test_modified_mkmks(self):
        font_a = mock_font()
        fea="""
            markClass [acutecomb gravecomb] <anchor 150 -10> @top;

            feature mark {
                pos mark @top
                 <anchor 85 354> mark @top;
            } mark;
            """
        font_a.builder.addOpenTypeFeatures(fea)
        font_a.recalc_tables()
        font_b = mock_font()
        fea="""
            markClass [acutecomb gravecomb] <anchor 0 -10> @top;

            feature mark {
                pos mark @top
                 <anchor 85 354> mark @top;
            } mark;
            """
        font_b.builder.addOpenTypeFeatures(fea)
        font_b.recalc_tables()
        diff = diff_marks(font_a, font_b, font_a.mkmks, font_b.mkmks, 'mkmks')
        modified = diff['modified']._data
        self.assertNotEqual(modified, [])
        self.assertEqual(len(modified), 4)


class TestKerns(unittest.TestCase):

    def test_missing_kerns(self):
        font_a = mock_font()
        fea="""
                feature kern {
                pos A V -120;
                pos V A -120;} kern;
            """
        font_a.builder.addOpenTypeFeatures(fea)
        font_a.recalc_tables()
        font_b = mock_font()
        diff = diff_kerning(font_a, font_b)
        missing = diff['missing']._data
        self.assertNotEqual(missing, [])
        # Missing and new kerns are only reported for matching glyphs
        # this is the same approach as the missing and new marks diff
        self.assertEqual(len(missing), 2)

    def test_modified_kerns(self):
        font_a = mock_font()
        fea="""
                feature kern {
                pos A V -120;} kern;
            """
        font_a.builder.addOpenTypeFeatures(fea)
        font_a.recalc_tables()

        font_b = mock_font()
        fea="""
                feature kern {
                pos A V -140;} kern;
            """
        font_b.builder.addOpenTypeFeatures(fea)
        font_b.recalc_tables()
        diff = diff_kerning(font_a, font_b)
        modified = diff['modified']._data
        self.assertNotEqual(modified, [])

    def test_upm_scale_modified_kerns(self):
        font_a = mock_font()
        font_a.builder.updateHead(unitsPerEm=1000)
        fea="""
                feature kern {
                pos A V -120;} kern;
            """
        font_a.builder.addOpenTypeFeatures(fea)
        font_a.recalc_tables()

        font_b = mock_font()
        font_b.builder.updateHead(unitsPerEm=2000)
        fea="""
                feature kern {
                pos A V -240;} kern;
            """
        font_b.builder.addOpenTypeFeatures(fea)
        font_b.recalc_tables()
        diff = diff_kerning(font_a, font_b)
        modified = diff['modified']._data
        self.assertEqual(modified, [])


class TestGDEF(unittest.TestCase):

    def test_bases(self):
        font_a = mock_font()
        fea_a="""
        markClass [acutecomb] <anchor 150 0> @top;

        feature mark {
            pos base [A Aacute]
             <anchor 100 300> mark @top;
        } mark;
        """
        font_a.builder.addOpenTypeFeatures(fea_a)
        font_a.recalc_tables()



        font_b = mock_font()
        fea_b="""
        markClass [acutecomb] <anchor 150 0> @top;

        feature mark {
            pos base [A] # Missing Aacute!
             <anchor 100 300> mark @top;
        } mark;
        """
        font_b.builder.addOpenTypeFeatures(fea_b)
        font_b.recalc_tables()
        # missing
        diff = diff_gdef_base(font_a, font_b)
        missing = diff['missing']._data
        self.assertEqual(len(missing), 1)
        # new
        diff = diff_gdef_base(font_b, font_a)
        new = diff['new']._data
        self.assertEqual(len(new), 1)

    def test_mark(self):
        font_a = mock_font()
        fea_a="""
        markClass [acutecomb gravecomb] <anchor 150 0> @top;

        feature mark {
            pos base [A]
             <anchor 100 300> mark @top;
        } mark;
        """
        font_a.builder.addOpenTypeFeatures(fea_a)
        font_a.recalc_tables()



        font_b = mock_font()
        fea_b="""
        markClass [acutecomb] <anchor 150 0> @top; # missing gravecomb!

        feature mark {
            pos base [A]
             <anchor 100 300> mark @top;
        } mark;
        """
        font_b.builder.addOpenTypeFeatures(fea_b)
        font_b.recalc_tables()
        # missing
        diff = diff_gdef_mark(font_a, font_b)
        missing = diff['missing']._data
        self.assertEqual(len(missing), 1)
        # new
        diff = diff_gdef_mark(font_b, font_a)
        new = diff['new']._data
        self.assertEqual(len(new), 1)



class TestDiffFonts(unittest.TestCase):

    def test_to_diff_categories(self):
        font_a = mock_font()
        font_b = mock_font()
        diff = DiffFonts(font_a, font_b, settings=dict(to_diff=['names', 'attribs']))
        self.assertEqual(len(diff._data.keys()), 2)

        diff = DiffFonts(font_a, font_b, settings=dict(to_diff=['names']))
        self.assertEqual(len(diff._data.keys()), 1)

        diff = DiffFonts(font_a, font_b, settings=dict(to_diff=["*"]))
        self.assertGreaterEqual(len(diff._data.keys()), 7)

        diff = DiffFonts(font_a, font_b, settings=dict(to_diff=["*", "glyphs"]))
        self.assertGreaterEqual(len(diff._data.keys()), 7)


if __name__ == '__main__':
    unittest.main()

