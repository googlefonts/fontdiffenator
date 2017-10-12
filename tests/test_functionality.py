"""
Use pyftsubset and ttx file manipulations to test gfdiff.diff_fonts
"""
import os
from glob import glob
from copy import copy
from fontTools.ttLib import TTFont
from nototools.glyph_area_pen import GlyphAreaPen
from diffenator.diff import diff_fonts, DIFF_THRESH
import unittest
import subprocess
import re
import shutil


class EnvSetup(unittest.TestCase):

    def setUp(self):
        self.path = os.path.dirname(__file__)
        self.data_path = os.path.join(self.path, 'data')
        self.font_path = os.path.join(self.data_path, 'Montserrat-Thin.ttf')
        self.modified_path = os.path.join(self.data_path, '_Montserrat-Thin.Modified.ttf')

    def tearDown(self):
        """Remove test data"""
        testdata_paths = os.path.join(self.data_path, '_*')
        testdata = glob(testdata_paths)
        map(os.remove, testdata)


class TestShape(EnvSetup):

    def test_ignore_shape_threshold(self):
        """We want to ignore changes which are less than half the dot of
        Montserrat Thin's 'i'. Half an i dot in Montserrat Thin is
        -1057.5000000000025."""
        ttfont = TTFont(self.font_path)
        glyphset = ttfont.getGlyphSet(ttfont)
        pen = GlyphAreaPen(glyphset)
        glyphset['uni0307'].draw(pen)
        area = pen.pop()
        # Notoshape diff always return positive integer
        self.assertEqual(DIFF_THRESH, abs(area) / 2)


class TestCompareFonts(EnvSetup):

    def _subset_font(self, params):
        subset_cmd = ["pyftsubset", self.font_path] +  params
        subprocess.call(subset_cmd)
        subset_font_path = os.path.join(self.data_path, 'Montserrat-Thin.subset.ttf')
        shutil.move(subset_font_path, self.modified_path)

    def test_new_kerning(self):
        """Use pyftsubset to strip the kerning out of a font"""
        self._subset_font(["--glyphs=*", "--layout-features-=kern"])

        font_a = self.modified_path
        font_b = self.font_path

        comparison = diff_fonts(font_a, font_b, rendered_diffs=False)
        self.assertNotEqual([], comparison['kerning']['new'])

    def test_missing_kerning(self):
        """Use pyftsubset to strip the kerning out of a font"""
        self._subset_font(["--glyphs=*", "--layout-features-=kern"])

        font_a = self.font_path
        font_b = self.modified_path

        comparison = diff_fonts(font_a, font_b, rendered_diffs=False)
        self.assertNotEqual([], comparison['kerning']['missing'])
        
    def test_modified_kerning(self):

        ttfont = TTFont(self.font_path)
        # Go through nested hell and modify the first kern
        ttfont['GPOS'].table.LookupList.Lookup[0].SubTable[0].PairSet[0].PairValueRecord[0].Value1.XAdvance = 200
        ttfont.save(self.modified_path)

        font_a = self.font_path
        font_b = self.modified_path

        comparison = diff_fonts(font_a, font_b, rendered_diffs=False)
        self.assertNotEqual([], comparison['kerning']['modified'])

    def test_new_glyphs(self):
        """Subset our souce font so it only contains 100 glyphs using
        pyftsubset"""        
        self._subset_font(["--gids=0-100"])

        font_a = self.modified_path
        font_b = self.font_path
        
        comparison = diff_fonts(font_a, font_b, rendered_diffs=False)
        self.assertNotEqual([], comparison['charset']['new'])

    def test_missing_glyphs(self):
        self._subset_font(["--gids=0-100"])

        font_a = self.font_path
        font_b = self.modified_path
        
        comparison = diff_fonts(font_a, font_b, rendered_diffs=False)
        self.assertNotEqual([], comparison['charset']['missing'])

    def test_modified_glyphs(self):
        ttfont = TTFont(self.font_path)
        ttfont['glyf']['a'] = ttfont['glyf']['b']
        ttfont.save(self.modified_path)

        font_a = self.font_path
        font_b = self.modified_path

        comparison = diff_fonts(font_a, font_b, rendered_diffs=True)
        self.assertNotEqual([], comparison['charset']['modified'])

    def test_modified_metrics(self):
        """Change the sidebearings of the A"""
        ttfont = TTFont(self.font_path)
        ttfont['hmtx'].metrics["a"] = (0, 0) # set advance width and lsb to 0
        modified_path = os.path.join(self.data_path, '_Montserrat-Thin-Metrics-Mod.ttf')
        ttfont.save(modified_path, reorderTables=False)

        font_a = self.font_path
        font_b = modified_path

        comparison = diff_fonts(font_a, font_b, rendered_diffs=False)
        self.assertNotEqual([{}], comparison['metrics']['modified'])

    def test_new_gsub(self):
        """Use pyftsubset to strip out the pnum feature"""
        self._subset_font(["--glyphs=*", "--layout-features-=pnum"])

        font_a = self.modified_path
        font_b = self.font_path

        comparison = diff_fonts(font_a, font_b, rendered_diffs=False)
        self.assertNotEqual([], comparison['gsub']['new'])

    def test_missing_gsub(self):

        self._subset_font(["--glyphs=*", "--layout-features-=pnum"])

        font_a = self.font_path
        font_b = self.modified_path

        comparison = diff_fonts(font_a, font_b, rendered_diffs=False)
        self.assertNotEqual([], comparison['gsub']['missing'])

#     TODO: (M4rc1e)
#     def test_new_marks(self):
#         pass

#     def test_missing_marks(self):
#         pass

#     def test_modified_marks(self):
#         pass


if __name__ == '__main__':
    unittest.main()
