import unittest
from diffenator.diff import subtract, modified


class TestHelperFunctions(unittest.TestCase):

    def setUp(self):       
        self.a = [
            {'glyph': 'a', 'x': 0, 'y': 0, 'kern_class': ['shoulder']},
            {'glyph': 'b', 'x': -5, 'y': 0, 'kern_class': ['shoulder']}
        ]

        self.b = [
            {'glyph': 'a', 'x': 100, 'y': 0, 'kern_class': ['shoulder']},
            {'glyph': 'b', 'x': 0, 'y': 0, 'kern_class': ['shoulder']},
            {'glyph': 'c', 'x': 30, 'y': 0, 'kern_class': ['shoulder']}
        ]

    def test_subtract(self):
        new = subtract(self.b, self.a, ['glyph', 'kern_class'])
        self.assertEqual(new[0]['glyph'], 'c')
        self.assertEqual(len(new), 1)

    def test_modified(self):
        modified_items = modified(self.a, self.b, ['glyph', 'kern_class'])
        modified_glyphs = ['a', 'b']
        for item in modified_items:
            self.assertIn(item['glyph'], modified_glyphs)

if __name__ == '__main__':
    unittest.main()
