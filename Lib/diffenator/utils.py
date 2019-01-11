import subprocess
from PIL import Image
from fontTools.varLib.mutator import instantiateVariableFont
try:
    from StringIO import StringIO
except ImportError:  # py3 workaround
    from io import BytesIO as StringIO


def render_string(font, string, features=None, pt_size=128):
    """Use Harfbuzz to render a string"""

    cmd = ['hb-view', '--font-size=%d' % pt_size]
    if font.instance_coordinates:
        location = ''
        for axis, val in font.instance_coordinates.items():
            location += '{}={}, '.format(axis, val)
        cmd += ['--variations=%s' % location]
    if features:
        # ignore aalt tag. This feat is used so users can access glyphs
        # via a glyph pallette.
        # https://typedrawers.com/discussion/1319/opentype-aalt-feature
        # glyphsapp will autogen this feature
        cmd += ['--features=%s' % ','.join(features).replace("aalt,", "")]
    cmd += [font.path, u'{}'.format(string)]
    try:
        img = StringIO(subprocess.check_output(cmd))
        return Image.open(img)
    except FileNotFoundError:
        raise OSError(
            "hb-view was not found. Check if Harbuzz is installed."
        )

