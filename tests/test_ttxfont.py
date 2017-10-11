from diffenator.ttxfont import TTXFont
import os
import unittest


class EnvSetup(unittest.TestCase):
    def setUp(self):
        self.path = os.path.dirname(__file__)
        self.data_path = os.path.join(self.path, 'data')
        self.font_path = os.path.join(self.data_path, 'Montserrat-Thin.ttf')
        self.font = TTXFont(self.font_path)
        self.attribs = [
            "base_anchors", 
            "mark_anchors", 
            "class_anchors", 
            "kern_classes", 
            "kern_values", 
            "gsub_rules",
        ]


class TestNewAttribs(EnvSetup):

    def test_attribs_exist(self):
        for attrib in self.attribs:
            self.assertEqual(True, hasattr(self.font, attrib))
    
    def test_attribs_are_not_empty(self):
        for attrib in self.attribs:
            self.assertNotEqual([], getattr(self.font, attrib)),


class TestOldAttribs(EnvSetup):
    """Since TTXFont inherits from fontTools.ttLib.TTFont make sure the old
        methods and attribs are intact"""
    def test_old_attribs(self):
        self.assertNotEqual(0, len(self.font['glyf'].keys()))
        self.assertNotEqual({}, self.font['cmap'].getcmap(3,1).cmap)


class TestParsing(EnvSetup):
    """For each funciton, monkey path ttxfont text then reparse it"""
    def test_parse_base_anchors(self):
        self.font.text = '''
        pos base [Napostrophe]
           <anchor 0 0> mark @uni0335_3_uni0336_mark;
        pos base [Tdieresis.ss01]
          <anchor 301 879> mark @acutecomb_98_uni0326.alt_mark
           <anchor 301 0> mark @dotbelowcomb_10_uni0331_mark
           <anchor 0 0> mark @uni0328_uni0328.curve_mark
           <anchor 0 0> mark @caroncomb.alt_4_uni031B.o_mark
           <anchor 301 350> mark @uni0335_3_uni0336_mark;
        '''
        self.font._parse_anchors()
        self.assertEqual(6, len(self.font.base_anchors))

    def test_parse_kern_classes(self):
        self.font.text = '''
        # Class definitions *********************************
        @D = [ D Dcaron Dcroat];
        @F = [ F F.sc];

        pos @D [period] -34;
        pos @F.sc @A_13_uni0202 -145;
        '''
        self.font._parse_kerning()

        f_class = '@F' in self.font.kern_classes
        self.assertEqual(True, f_class)
        self.assertEqual(3, len(self.font.kern_classes['@D']))

    def test_parse_kern_values(self):
        self.font.text = '''
        # Class definitions *********************************
        @D = [ D Dcaron Dcroat];
        @F = [ F F.sc];

        pos @D [period] -34;
        pos @F.sc @A_13_uni0202 -145;
        pos A V -45;
        pos A Y -60;
        '''
        self.font._parse_kerning()
        self.assertEqual(4, len(self.font.kern_values))

    def test_parse_gsub_rules(self):
        self.font.text = '''
        feature ordn {
            sub A from [a.sc ordfeminine];
            sub O from [o.sc ordmasculine];
        } ordn;

        feature c2sc {
            sub A by a.sc;
            sub B by b.sc;
        } c2sc;
        '''
        self.font._parse_gsub()
        # groups are flattened
        self.assertEqual(6, len(self.font.gsub_rules))


if __name__ == '__main__':
    unittest.main()
