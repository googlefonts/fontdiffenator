"""
Parser for a font's OpenType features. This approach is not ideal
we need to wait for fontTool's Otib to be fully implemented.

This module uses regex on ttx files to create python serialisable
OT methods/attribs.
"""

from fontTools.ttLib import TTFont
from collections import namedtuple
import re
import subprocess
import tempfile


__all__ = ['TTXFont']


class TTXFont(TTFont):
    """Extend fontTool's TTFont object so gsub and gpos tables
    are easier to manipulate.

    Gsub and Gpos tables are parsed using ttx and regex.

    This should be deprecated when
    https://github.com/fonttools/fonttools/issues/468 is implemented
    properly. The object api endpoints will also change when this
    happens so we should refactor."""
    def __init__(self, file):
        super(TTXFont, self).__init__(file)
        self.file = file
        ttxn_file = tempfile.NamedTemporaryFile()
        subprocess.call(['ttxn', '-q', '-t', 'GPOS', '-t', 'GSUB',
                         '-o', ttxn_file.name, '-f', self.file])
        self.text = ttxn_file.read()
        self._base_anchors = []
        self._mark_anchors = []
        self._class_anchors = []
        self._parse_anchors()
        
        self._kern_classes = {}
        self._kern_values = []
        self._parse_kerning()

        self._gsub_rules = []
        self._parse_gsub()

    def _parse_anchors(self):
        rx_glyphs = re.compile('mark \[([\w\d\s@_.]+)\]')
        rx_anchor = re.compile(r'<anchor ([0-9]{1,5}) ([0-9]{1,5})> '
                                'mark (@[\w\d_.]+)')

        self._anchors_class = self._parse_anchor_info(
            self.text, rx_glyphs, rx_anchor
        )

        for t in ('base', 'mark'):
            rx_glyphs = re.compile(r'pos %s \[(.*)\]' % t)
            rx_anchor = re.compile(r'<anchor ([0-9]{1,5}) ([0-9]{1,5})> '
                                    'mark (@[\w\d_.]+)')

            mark_type = '_anchors_%s' % t
            setattr(self, mark_type, self._parse_anchor_info(
                self.text, rx_glyphs, rx_anchor)
            )

    def _parse_anchor_info(self, text,  rx1, rx2):
        anchor_rules = []
        Anchor = namedtuple('Anchor', ['glyph', 'group', 'x', 'y'])
        current_glyphs = None
        for line in text.split('\n'):
            glyphs = rx1.search(line)
            anchor = rx2.search(line)

            if glyphs:
                current_glyphs = glyphs
            if anchor and current_glyphs:
                parsed = current_glyphs.groups() + anchor.groups()
                glyph, x, y, group = parsed
                anchor_rules.append(Anchor(glyph, group, int(x), int(y)))
        return anchor_rules

    def _parse_kerning(self):
        rx = re.compile(r'(@[\w\d_.]+) = \[([\s\w\d_.]+)\];')
        self._parse_kerning_classes(rx)

        rx = re.compile('pos \[?([\w\d@_.]+)\]? \[?([\w\d@_.]+)\]? (-?\d+);')
        self._parse_kerning_values(rx)

    def _parse_kerning_classes(self, rx):
        """Parse kerning class definitions."""
        kern_classes = {}
        for definition in rx.findall(self.text):
            name, members = definition
            kern_classes[name] = members.split()
        self._kern_classes = kern_classes

    def _parse_kerning_values(self, rx):
        """Parse kerning rules with flattened output"""
        kern_values = []
        Kern = namedtuple('Kern', ['left', 'right', 'value'])
        for rule in rx.findall(self.text):
            # print rule
            left, right, val = rule
            val = int(val)
            if left in self.kern_classes:
                left = self.kern_classes[left]
            else:
                left = [left]
            if right in self.kern_classes:
                right = self.kern_classes[right]
            else:
                right = [right]
            kern_values.append(
                Kern(left, right, val)
            )
        self._kern_values = kern_values

    def _parse_gsub(self):
        """
        Parse the ttxn GSUB table in the following manner:

        1. Get features
        2. Get feature content
        3. Extract lookup rules from feature content

        Following substitutions are currently implemented:
        - Type 1: Single substitutions
        - Type 2: Multiple substitutions
        - Type 3: Alternate substitutions
        - Type 4: Ligature substitutionss

        TODO (m4rc1e): LookupTypes 5, 6, 8 still need implementing
        """
        rules = []
        features = self._get_gsub_features()
        for feature in features:
            content = self._get_feature_content(feature)
            lookups_rules = self._get_lookups_rules(content[0], feature)
            rules += lookups_rules
        self._gsub_rules = rules

    def _get_gsub_features(self):
        features = set()
        feature_name_rx = r'feature (\w+) {'

        for name in re.findall(feature_name_rx, self.text):
            features.add(name)
        return list(features)

    def _get_feature_content(self, feature):
        contents_rx = r'feature %s {(.*?)} %s;'
        contents = re.findall(contents_rx % (feature, feature), self.text, re.S)
        return contents

    def _get_lookups_rules(self, content, feature):
        """Ignore rules which use "'". These are contextual and not in
        lookups 1-4"""
        rule_rx = r"[^C] sub (.*[^\']) (by|from) (.*);"
        rules = re.findall(rule_rx, content)
        parsed_rules = self._parse_gsub_rules(rules, feature)
        return parsed_rules

    def _parse_gsub_rules(self, rules, feature):
        """
        Parse GSUB sub LookupTypes 1, 2, 3, 4, 7. Return list of tuples with
        the following tuple sequence.

        (feature, [input glyphs], operator, [output glyphs])

        Type 1 Single Sub:
        sub a by a.sc;
        sub b by b.sc;
        [
            (feat, ['a'], 'by' ['a.sc']),
            (feat, ['b'], 'by' ['b.cs'])
        ]


        Type 2 Multiple Sub:
        sub f_f by f f;
        sub f_f_i by f f i;
        [
            (feat, ['f_f'], 'by', ['f', 'f']),
            (feat, ['f_f_i'], 'by', ['f', 'f', 'i'])
        ]

        Type 3 Alternative Sub:
        sub ampersand from [ampersand.1 ampersand.2 ampersand.3];
            [
                (feat, ['ampersand'], 'from', ['ampersand.1']),
                (feat, ['ampersand'], 'from', ['ampersand.2']),
                (feat, ['ampersand'], 'from', ['ampersand.3'])
            ]

        Type 4 Ligature Sub:
        sub f f by f_f;
        sub f f i by f_f_i;
        [
            (feat, ['f', 'f'] 'by' ['f_f]),
            (feat, ['f', 'f', 'i'] 'by' ['f_f_i'])
        ]

        http://www.adobe.com/devnet/opentype/afdko/topic_feature_file_syntax.html#4.e
        """
        parsed = []
        Rule = namedtuple('Rule', ['feature', 'input', 'operator', 'result'])
        for idx, (left, op, right) in enumerate(rules):

            left_group, right_group = [], []
            if left.startswith('[') and left.endswith(']'):
                left = self._gsub_rule_group_to_string(left)

            if right.startswith('[') and right.endswith(']'):
                right = self._gsub_rule_group_to_string(right)

            if op == 'by': # parse LookupType 1, 2, 4
                parsed.append(Rule(feature, left.split(), op, right.split()))
            elif op == 'from': # parse LookupType 3
                for glyph in right.split(): # 'a.alt a.sc' -> ['a.alt', 'a.sc']
                    parsed.append(Rule(feature, left.split(), op, right.split()))
        return parsed

    def _gsub_rule_group_to_string(self, seq):
        """[a a.sc a.sups] --> 'a a.sc a.sups'"""
        return seq[1:-1]

    @property
    def base_anchors(self):
        return self._anchors_base

    @property
    def mark_anchors(self):
        return self._anchors_mark

    @property
    def class_anchors(self):
        return self._anchors_class

    @property
    def kern_classes(self):
        return self._kern_classes

    @property
    def kern_values(self):
        return self._kern_values

    @property
    def gsub_rules(self):
        return self._gsub_rules
