__version__ = "0.5.1"
import sys
if sys.version_info[0] < 3 and sys.version_info[1] < 6:
    raise ImportError("Visualize module requires Python3.6+!")
from array import array
from PIL import Image
from ctypes import cast, memmove, CDLL, c_void_p, c_int
from sys import byteorder
from cairo import Context, ImageSurface, FORMAT_A8, FORMAT_ARGB32
from freetype.raw import *
import uharfbuzz as hb
import os
import shutil
import tempfile
try:
    from StringIO import StringIO
except ImportError:  # py3 workaround
    from io import BytesIO as StringIO
if sys.version_info.major == 3:
    unicode = str

CHOICES = [
    'names',
    'marks',
    'mkmks',
    'attribs',
    'metrics',
    'glyphs',
    'kerns'
]

class Tbl:

    def __init__(self, table_name, data=None, renderable=False):
        if not data:
            self._data = []
        else:
            self._data = data
        self.table_name = table_name
        self.renderable = renderable
        self._report_columns = None

    def append(self, item):
        self._data.append(item)
        if not self._report_columns:
            self._report_columns = item.keys()

    def report_columns(self, items):
        """Columns to display in report"""
        self._report_columns = items

    def to_txt(self, limit=50, strings_only=False, dst=None):
        return self._report(TXTFormatter, limit, strings_only, dst)

    def to_md(self, limit=50, strings_only=False, dst=None):
        return self._report(MDFormatter, limit, strings_only, dst)

    def _report(self, formatter, limit=50, strings_only=False, dst=None):
        """Generate a report for a table.

        Parameters
        ----------
        formatter: Formatter
            Text formatter to use for report
        strings_only: bool
            If True only return the character combos.

        Returns
        -------
        str
        """
        report = formatter()
        report.subsubheading(self.table_name)

        if strings_only and self.renderable:
            string = ' '.join([r['string'] for r in self._data[:limit]])
            report.paragraph(string)
        else:
            report.table_heading(self._report_columns)
            for row in self._data[:limit]:
                culled_row = []
                for name in self._report_columns:
                    culled_row.append(row[name])
                report.table_row(culled_row)

        if dst:
            with open(dst, 'w') as doc:
                doc.write("\n".join(report.text))
        return report.text

    def _to_png(self, font, font_position=None, dst=None,
                limit=800, size=1500):
        """Use HB, FreeType and Cairo to produce a png for a table.

        Parameters
        ----------
        font: DFont
        font_position: str
            Label indicating which font has been used. 
        dst: str
            Path to output image. If no path is given, return in-memory 
        """
        # TODO (M Foley) better packaging for pycairo, freetype-py
        # and uharfbuzz.
        # Users should be able to pip install these bindings without needing
        # to install the correct libs.

        # A special mention to the individuals who maintain these packages. Using
        # these dependencies has sped up the process of creating diff images
        # significantly. It's an incredible age we live in.
        tab = int(font.size / 25)
        width, height = 1024, 200

        # Compute height of image
        x, y, baseline = 20, 0, 0

        for row in self._data[:limit]:
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
        ctx.show_text("{}: {}".format(self.table_name, len(self._data)))
        ctx.move_to(20, 100)
        if font_position:
            ctx.show_text("Font Set: {}".format(font_position))
        if len(self._data) > limit:
            ctx.set_font_size(20)
            ctx.move_to(20, 150)
            ctx.show_text("Warning: {} different items. Only showing most serious {}".format(
                len(self._data), limit)
            )

        hb.ot_font_set_funcs(font.hbfont)

        # Draw glyphs
        x, y, baseline = 20, 200, 0
        x_pos = 20
        y_pos = 200
        for row in self._data[:limit]:
            buf = hb.Buffer.create()
            buf.add_str(row['string'])

            buf.guess_segment_properties()
            try:
                features = {f: True for f in row['features']}
                hb.shape(font.hbfont, buf, features)
            except KeyError:
                hb.shape(font.hbfont, buf)

            char_info = buf.glyph_infos
            char_pos = buf.glyph_positions
            for info, pos in zip(char_info, char_pos):
                gid = info.codepoint            
                font.ftfont.load_glyph(gid, flags=6)
                bitmap = font.ftslot.bitmap

                if bitmap.width > 0:
                    ctx.set_source_rgb(0, 0, 0)
                    glyph_surface = _make_image_surface(font.ftfont.glyph.bitmap, copy=False)
                    ctx.set_source_surface(glyph_surface,
                                           x_pos + font.ftslot.bitmap_left + (pos.x_offset / 64.),
                                           y_pos - font.ftslot.bitmap_top - (pos.y_offset / 64.))
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
        else:
            img = StringIO()
            Z.write_to_png(img)
            return Image.open(img)

    def sort(self, *args, **kwargs):
        self._data.sort(*args, **kwargs)

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        for i in self._data:
            yield i


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


class DiffTable(Tbl):

    def __init__(self, table_name, font_a, font_b,
                 data=None, renderable=False):
        super(DiffTable, self).__init__(table_name, data, renderable=renderable)
        self._font_a = font_a
        self._font_b = font_b

    def to_gif(self, dst):

        img_a = self._to_png(self._font_a, "Before")
        img_b = self._to_png(self._font_b, "After")

        img_a.save(
            dst,
            save_all=True,
            append_images=[img_b],
            loop=10000,
            duration=1000
        )

class DFontTable(Tbl):

    def __init__(self, font, table_name, renderable=False):
        super(DFontTable, self).__init__(table_name, renderable=renderable)
        self._font = font


class DFontTableIMG(DFontTable):

    def to_png(self, dst=None, limit=800):
        font = self._font
        return self._to_png(font, dst=dst, limit=limit)


class Formatter:
    """Base Class for formatters"""

    def __init__(self):
        self._text = []

    def heading(self, string):
        raise NotImplementedError()

    def subheading(self, string):
        raise NotImplementedError()

    def subsubheading(self, string):
        raise NotImplementedError()

    def table_heading(self, row):
        raise NotImplementedError()

    def table_row(self, row, clip_col=True):
        raise NotImplementedError()

    def linebreak(self):
        self._text.append('')

    def paragraph(self, string):
        self._text.append(string)

    @property
    def text(self):
        return '\n'.join(self._text)


class TXTFormatter(Formatter):
    """Formatter for CommandLines."""
    def heading(self, string):
        self._text.append('**{}**\n'.format(string))

    def subheading(self, string):
        self._text.append('***{}***\n'.format(string))

    def subsubheading(self, string):
        self._text.append('****{}****\n'.format(string))

    def table_heading(self, row):
        header = unicode("{:<20}" * len(row))
        header = header.format(*tuple(row))
        self._text.append(header)

    def table_row(self, row, clip_col=True):
        row = map(str, row)
        if clip_col:
            _row = []
            for item in row:
                if len(item) >= 16:
                    item = item[:16] + "..."
                _row.append(item)
            row = _row
        t_format = unicode("{:<20}" * len(row))
        row = t_format.format(*tuple(row))
        self._text.append(row)


class MDFormatter(Formatter):
    """Formatter for Github Markdown"""
    def heading(self, string):
        self._text.append('# {}\n'.format(string))

    def subheading(self, string):
        self._text.append('## {}\n'.format(string))

    def subsubheading(self, string):
        self._text.append('### {}\n'.format(string))

    def table_heading(self, row):
        string = ' | '.join(row)
        string += '\n'
        string += '--- | ' * len(row)
        self._text.append(string)

    def table_row(self, row):
        row = map(str, row)
        string = ' | '.join(row)
        self._text.append(string)

