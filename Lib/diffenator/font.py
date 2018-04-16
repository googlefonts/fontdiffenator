from fontTools.ttLib import TTFont
from inputgen import InputGenerator


class InputFont(TTFont):
    """Wrapper for TTFont object which contains an input map to generate
    a glyph. This object will be deprecated once otLib progresses"""
    def __init__(self, file):
        super(InputFont, self).__init__(file)
        self._input_map = self._gen_inputs()

    @property
    def input_map(self):
        return self._input_map

    def _gen_inputs(self):
        inputs = InputGenerator(self).all_inputs()
        return {g.name: g for g in inputs}
