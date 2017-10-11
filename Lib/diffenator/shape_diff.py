"""
Change output for Nototool's shape diff to suite GF requirements.
"""
from nototools.shape_diff import ShapeDiffFinder


class ShapeDiffFinder(ShapeDiffFinder):

    def cleanup(self):
        if self.stats['unmatched']:
            self.stats['unmatched'].pop(0)
        if self.stats['untested']:
            self.stats['untested'] = [i[1] for i in self.stats['untested']]
        if self.stats['compared']:
            self.stats['compared'] = [(i[1], i[0]) for i in self.stats['compared']]
