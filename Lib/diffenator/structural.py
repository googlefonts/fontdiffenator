from diffenator import DiffTable
from fontTools.misc.fixedTools import floatToFixedToStr
from fontTools.misc.timeTools import timestampToString


def structural_diff(left, right):
    lefttables = set(left.ttfont.keys())
    righttables = set(right.ttfont.keys())
    results = {}

    directory = DiffTable("OpenType Table Directory", left, right)
    directory.report_columns(["table", "before", "after"])
    for t in sorted(list(lefttables | righttables)):
        if not (t in left.ttfont and t in right.ttfont):
            directory.append(
                {
                    "table": t,
                    "before": ("X" if t in left.ttfont else ""),
                    "after": ("X" if t in right.ttfont else ""),
                }
            )
        diffclass = "Diff_%s" % t.replace("/", "_")  # OS/2. :-(
        if diffclass in globals():
            differ = globals()[diffclass]
            diff = differ(left, right, t).diff()
            if diff:
                results[t] = diff
    results["directory"] = directory
    return results


def _format_panose(panose):
    return ",".join(
        {"%s=%i" % (k[1:], getattr(panose, k)) for k in sorted(panose.__dict__.keys())}
    )


def bitfield(n):
    return lambda x: ("{0:0" + str(n) + "b}").format(x)


class OTTableDiffer:
    fields = []
    skip_fields = []
    use_dict_for_fields = True
    field_formatters = {
        "fontRevision": lambda x: floatToFixedToStr(x, 16),
        "tableVersion": lambda x: floatToFixedToStr(x, 16),
        "created": timestampToString,
        "flags": bitfield(16),
        "panose": _format_panose,
        "macStyle": bitfield(16),
        "ulUnicodeRange1": bitfield(32),
        "ulUnicodeRange2": bitfield(32),
        "ulUnicodeRange3": bitfield(32),
        "ulUnicodeRange4": bitfield(32),
    }

    def __init__(self, left, right, tablename):
        self.left = left
        self.right = right
        self.tablename = tablename

    def prepdiff(self):
        self.diffreport = DiffTable("%s table" % self.tablename, self.left, self.right)
        self.diffreport.report_columns(["field", "before", "after"])
        self.lefttable = self.left.ttfont[self.tablename]
        self.righttable = self.right.ttfont[self.tablename]

    def diff(self):
        self.prepdiff()
        fields = self.fields
        if self.use_dict_for_fields:
            fields = set(self.lefttable.__dict__.keys()) & set(
                self.righttable.__dict__.keys()
            )

        for field in fields:
            if field in self.skip_fields:
                continue
            if not (hasattr(self.lefttable, field) and hasattr(self.righttable, field)):
                continue
            leftattr = getattr(self.lefttable, field)
            rightattr = getattr(self.righttable, field)
            if field in self.field_formatters:
                leftattr = self.field_formatters[field](leftattr)
                rightattr = self.field_formatters[field](rightattr)
            if leftattr != rightattr:
                self.diffreport.append(
                    {"field": field, "before": leftattr, "after": rightattr}
                )
        return self.diffreport


class Diff_head(OTTableDiffer):
    skip_fields = [
        "checkSumAdjustment",
        "magicNumber",
        "modified",
    ]


class Diff_hhea(OTTableDiffer):
    pass


class Diff_maxp(OTTableDiffer):
    pass


class Diff_OS_2(OTTableDiffer):
    pass


class Diff_post(OTTableDiffer):
    pass


class Diff_vhea(OTTableDiffer):
    pass


class Diff_fvar(OTTableDiffer):
    def diff(self):
        self.prepdiff()
        axes_left = {axis.axisTag: axis for axis in self.lefttable.axes}
        axes_right = {axis.axisTag: axis for axis in self.righttable.axes}
        alltags = set(axes_left.keys()) & set(axes_right.keys())
        for tag in alltags:
            if not (tag in axes_left and tag in axes_right):
                self.diffreport.append(
                    {
                        "field": tag + " axis",
                        "before": ("X" if tag in axes_left else ""),
                        "after": ("X" if tag in axes_right else ""),
                    }
                )
                continue
            axis_left = self._format_axis(axes_left[tag])
            axis_right = self._format_axis(axes_right[tag])
            for key in axis_left.keys():
                if axis_left[key] != axis_right[key]:
                    self.diffreport.append(
                        {
                            "field": key,
                            "before": axis_left[key],
                            "after": axis_right[key],
                        }
                    )
        return self.diffreport

    def _format_axis(self, axis):
        tag = axis.axisTag
        return {
            tag + " flags": "0x%X" % axis.flags,
            tag + " MinValue": floatToFixedToStr(axis.minValue, 16),
            tag + " DefaultValue": floatToFixedToStr(axis.defaultValue, 16),
            tag + " MaxValue": floatToFixedToStr(axis.maxValue, 16),
            tag + " AxisNameID": str(axis.axisNameID),
        }


class Diff_avar(OTTableDiffer):
    def diff(self):
        if "fvar" not in self.left.ttfont or "fvar" not in self.right.ttfont:
            return
        self.prepdiff()

        self.diffreport.report_columns(["axis", "before", "after"])

        axisTagsleft = [axis.axisTag for axis in self.left.ttfont["fvar"].axes]
        axisTagsright = [axis.axisTag for axis in self.right.ttfont["fvar"].axes]

        def _seg_to_str(segtuple):
            k, v = segtuple
            return "%s => %s" % (floatToFixedToStr(k, 14), floatToFixedToStr(v, 14))

        for tag in set(axisTagsright) & set(axisTagsleft):
            lsegs = list(self.lefttable.segments.get(tag, {}).items())
            rsegs = list(self.righttable.segments.get(tag, {}).items())
            if len(lsegs) != len(rsegs):
                self.diffreport.append(
                    {
                        "axis": tag,
                        "before": "%i segments" % len(lsegs),
                        "after": "%i segments" % len(rsegs),
                    }
                )
            for i in range(max(len(lsegs), len(rsegs)) + 1):
                lseg = _seg_to_str(lsegs[i]) if i < len(lsegs) else "No mapping"
                rseg = _seg_to_str(rsegs[i]) if i < len(rsegs) else "No mapping"
                if lseg != rseg:
                    self.diffreport.append({"axis": tag, "before": lseg, "after": rseg})
        return self.diffreport
