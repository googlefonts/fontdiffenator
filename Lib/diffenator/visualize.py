"""Generate images from diff tables.

Users must have Harfbuzz, FreeType and Cairo installed to use this module.
See README.md for installation instructions.

This module only works for Python3. Uharfbuzz uses python Types."""
import sys
if sys.version_info[0] < 3 and sys.version_info[1] < 6:
    raise ImportError("Vizualize module requires Python3.6+!")
from array import array
from PIL import Image
from ctypes import cast, memmove, CDLL, c_void_p, c_int
from sys import byteorder
import freetype
from freetype.raw import *
from freetype import FT_PIXEL_MODE_MONO, FT_PIXEL_MODE_GRAY, FT_Pointer, FT_Bitmap, FT_Fixed, FT_Set_Var_Design_Coordinates
from cairo import Context, ImageSurface, FORMAT_A8, FORMAT_ARGB32
import uharfbuzz as hb
import os
import shutil
import tempfile
from diffenator.font import InputFont
from diffenator.diff import diff_fonts
try:
    from StringIO import StringIO
except ImportError:  # py3 workaround
    from io import BytesIO as StringIO


def _make_image_surface(bitmap, copy=True):
    """Convert FreeType bitmap to Cairo ImageSurface.

    Special thanks to Hintak and his example code:
    https://github.com/rougier/freetype-py/blob/master/examples/bitmap_to_surface.py


    TODO (M Foley) understand this better and see if a more elegant
    solution exists."""
    content = bitmap._FT_Bitmap
    cairo_format = FORMAT_A8

    src_pitch = content.pitch
    dst_pitch = ImageSurface.format_stride_for_width(cairo_format, content.width)

    pixels = _to_array(content, content.pixel_mode, dst_pitch)
    result = ImageSurface.create_for_data(
        pixels, cairo_format,
        content.width, content.rows,
        dst_pitch)
    return result


def _to_array(content, pixel_mode, dst_pitch):
    buffer_size = content.rows * dst_pitch
    buff = array("B", b"0" * buffer_size)
    dstaddr = buff.buffer_info()[0]
    srcaddr = cast(content.buffer, FT_Pointer).value
    src_pitch = content.pitch

    for i in range(content.rows) :
        memmove(dstaddr, srcaddr, src_pitch)
        dstaddr += dst_pitch
        srcaddr += src_pitch
    return buff


def render_table(font, diff_table, size=1500,
                 title=None, font_position=None, item_limit=800, dst=None):
    """Use HB, FreeType and Cairo to produce a png for a table.

    TODO (M Foley) better packaging for pycairo, freetype-py and uharfbuzz.
    Users should be able to pip install these bindings without needing to
    install the correct libs.

    A special mention to the individuals who maintain these packages. Using
    these dependencies has sped up the process of creating diff images
    significantly. It's an incredible age we live in.


    Parameters
    ----------
    font: InputFont
    diff_table: list[dict, ...]
    title: str
        Title of image
    font_position: str
        Label indicating which font has been used. 
    dst: str
        Path to output image. If no path is given, return in-memory 
    """
    ft_font = freetype.Face(font.path)
    slot = ft_font.glyph

    upm_size = size

    tab = int(size / 25)
    width, height = 1024, 200
    if font.is_variable:
        coords = []
        for name in font.axis_order:
            coord = FT_Fixed(int(font.axis_locations[name]) << 16)
            coords.append(coord)
        ft_coords = (FT_Fixed * len(coords))(*coords)
        FT_Set_Var_Design_Coordinates(ft_font._FT_Face, len(ft_coords), ft_coords)
    ft_font.set_char_size(upm_size)

    # Compute height of image
    x, y, baseline = 20, 0, 0

    for row in diff_table[:item_limit]:
        x += tab

        if x > (width - 20):
            y += tab
            x = 20
    height += y
    height += 100

    # draw image
    Z = ImageSurface(FORMAT_ARGB32, width, height)
    ctx = Context(Z)
    ctx.rectangle(0, 0, width, height)
    ctx.set_source_rgb(1, 1, 1)
    ctx.fill()

    # label image
    ctx.set_font_size(30)
    ctx.set_source_rgb(0.5, 0.5, 0.5)
    ctx.move_to(20, 50)
    if title:
        ctx.show_text("{}: {}".format(title, len(diff_table)))
    ctx.move_to(20, 100)
    if font_position:
        ctx.show_text("Font Set: {}".format(font_position))
    if len(diff_table) > item_limit:
        ctx.set_font_size(20)
        ctx.move_to(20, 150)
        ctx.show_text("Warning: {} different items. Only showing most serious {}".format(
            len(diff_table), item_limit)
        )

    # HB font
    hb_face = hb.Face.create(open(font.path, 'rb').read())
    hb_font = hb.Font.create(hb_face)
    hb_upem = upm_size

    hb_font.scale = (hb_upem, hb_upem)
    if font.is_variable:
        hb_font.set_variations(font.axis_locations)
    hb.ot_font_set_funcs(hb_font)

    # Draw glyphs
    x, y, baseline = 20, 200, 0
    x_pos = 20
    y_pos = 200
    for row in diff_table[:item_limit]:

        buf = hb.Buffer.create()
        buf.add_str(row['string'])

        buf.guess_segment_properties()
        try:
            features = {f: True for f in row['features']}
            hb.shape(hb_font, buf, features)
        except KeyError:
            hb.shape(hb_font, buf)

        char_info = buf.glyph_infos
        char_pos = buf.glyph_positions
        for info, pos in zip(char_info, char_pos):
            gid = info.codepoint            
            ft_font.load_glyph(gid, flags=6)
            bitmap = slot.bitmap

            if bitmap.width > 0:
                ctx.set_source_rgb(0, 0, 0)
                glyph_surface = _make_image_surface(ft_font.glyph.bitmap, copy=False)
                ctx.set_source_surface(glyph_surface,
                                       x_pos + slot.bitmap_left + (pos.x_offset / 64.),
                                       y_pos - slot.bitmap_top - (pos.y_offset / 64.))
                glyph_surface.flush()
                ctx.paint()
            x_pos += (pos.x_advance) / 64.
            y_pos += (pos.y_advance) / 64.

        x_pos += tab - (x_pos % tab)
        if x_pos > (width - 20):
            # add label
            if font_position:
                ctx.set_source_rgb(0.5, 0.5, 0.5)
                ctx.set_font_size(10)
                ctx.move_to(width - 20, y_pos)
                ctx.rotate(1.5708)
                ctx.show_text(font_position)
                ctx.set_source_rgb(0,0,0)
                ctx.rotate(-1.5708)
            # Start a new row
            y_pos += tab
            x_pos = 20
    Z.flush()
    if dst:
        Z.write_to_png(dst)
    # TODO (M Foley) GDB Debug segmentation fault. It only occurs on large
    # images.
    else:
        img = StringIO()
        Z.write_to_png(img)
        return Image.open(img)


def diff_render_table(font_a, font_b, diff_table, dst,
                      size=1500, title=None, item_limit=800):
    with tempfile.NamedTemporaryFile() as img_a_path, \
         tempfile.NamedTemporaryFile() as img_b_path:
        render_table(font_a, diff_table, size, title, 'Before', item_limit, dst=img_a_path)
        render_table(font_b, diff_table, size, title, 'After', item_limit, dst=img_b_path)

        with Image.open(img_a_path) as img_a, Image.open(img_b_path) as img_b:
            img_a.save(
                dst,
                save_all=True,
                append_images=[img_b],
                loop=10000,
                duration=1000
            )


def diff_render(font_a, font_b, diff_dict, dst, size=1500, item_limit=800):
    """Generate before and after gifs from a diff_fonts object.

    Parameters
    ----------
    font_a: InputFont
    font_b: InputFont
    diff_dict: list
        A diffenator.diff.diff_font object
    dst: str
        Path to output dir. Will create dir if it doesn't exist.
    """
    if not os.path.isdir(dst):
        os.mkdir(dst)
    else:
        shutil.rmtree(dst)
        os.mkdir(dst)
    renderable = ['glyphs', 'kerns', 'marks', 'mkmk', 'metrics']
    for cat in diff_dict:
        if cat not in renderable:
            continue
        for sub_cat in diff_dict[cat]:
            title = '{} {}'.format(cat.title(), sub_cat.title())
            filename = os.path.join(dst, '{}_{}.gif'.format(cat, sub_cat))
            diff = diff_dict[cat][sub_cat]
            if not len(diff) > 1:
                continue
            diff_render_table(font_a, font_b, diff, filename, size, title,
                              item_limit)
