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
    if font.axis_locations:
        location = ''
        for axis, val in font.axis_locations.items():
            location += '{}={}, '.format(axis, val)
        cmd += ['--variations=%s' % location]
    if features:
        cmd += ['--features=%s' % features]
    cmd += [font.path, u'{}'.format(string)]
    try:
        img = StringIO(subprocess.check_output(cmd))
        return Image.open(img)
    except FileNotFoundError:
        raise OSError(
            "hb-view was not found. Check if Harbuzz is installed."
        )
