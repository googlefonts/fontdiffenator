import subprocess
from PIL import Image
from fontTools.varLib.mutator import instantiateVariableFont
try:
    from StringIO import StringIO
except ImportError:  # py3 workaround
    from io import BytesIO as StringIO

__all__ = ['STYLE_TERMS', 'stylename_from_name',
           'vf_instance_from_static', 'vf_instance']

STYLE_TERMS = [
    'Hairline',
    'Thin',
    'ExtraLight',
    'UltraLight',
    'Light',
    'Regular',
    'Book',
    'Medium',
    'SemiBold',
    'Bold',
    'ExtraBold',
    'Black',
    'Italic',
    'Oblique',
    'SemiCondensed',
    'ExtraCondensed',
    'Condensed',
    'Expanded',
    'SemiExpanded',
    'Narrow',
    'Compressed',
    'Semi',
    'Demi',
    'Extra',
    'Ultra',
    'Demi',
]


def stylename_from_name(name):
    """Extract the stylename from a string e.g
    'Comforta ExtraBold Italic' --> 'ExtraBold Italic'

    Parameters
    ----------
    name: str

    Returns
    -------
    str"""
    string = []
    for i in name.split():
        if i.lower() in [s.lower() for s in STYLE_TERMS]:
            string.append(i)
    stylename = ' '.join(string)
    return stylename


def _axis_loc_from_name(vf_font, style_name):
    """Get VF axis location from a style name. Style_name terms will be filtered
    to only include terms which are in STYLE_TERMS"""
    vf_instance_idxs = [n.subfamilyNameID for n in vf_font['fvar'].instances]
    vf_instance_names = [vf_font['name'].getName(n, 3, 1, 1033).toUnicode()
                         for n in vf_instance_idxs]
    vf_instance_coords = {n: i.coordinates for n, i in
                          zip(vf_instance_names, vf_font['fvar'].instances)}
    if not vf_instance_coords:
        raise Exception('{} has no fvar instances'.format(vf_font.path))

    if style_name not in vf_instance_names:
        raise Exception(('Instance "{}"" not found in '
                         'fvar instances. Available [{}]'.format(
                          style_name, ', '.join(vf_instance_names))
        ))
    return vf_instance_coords[style_name]


def vf_instance_from_static(vf_font, static_font):
    """Instantiate a VF using a static font's nametable.
    Returned instance is in-memory

    Parameters
    ----------
    vf_font: InputFont
    static_font: InputFont

    Returns
    -------
    InputFont"""
    style_name = stylename_from_name(
            static_font['name'].getName(4, 3, 1, 1033).toUnicode()
    )
    if not style_name and static_font['name'].getName(17, 3, 1, 1033):
        style_name = static_font['name'].getName(17, 3, 1, 1033).toUnicode()
    if not style_name:
        style_name = static_font['name'].getName(2, 3, 1, 1033).toUnicode()
    print('Getting instance {}'.format(style_name))
    return vf_instance(vf_font, style_name)


def vf_instance(vf_font, instance_name):
    """Instantiate a VF using an instance name.
    Returned instance is in-memory.

    Parameters
    ----------
    vf_font: InputFont
    instance_name: str
        Terms used will be filtered through STYLE_TERMS. e.g
        'Comforta ExtraBold Italic' --> 'ExtraBold Italic'

    Returns
    -------
    InputFont"""
    loc = _axis_loc_from_name(vf_font, instance_name)
    instance = instantiateVariableFont(vf_font, loc, inplace=True)
    instance.is_variable = True
    instance.axis_locations = loc
    return instance


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
