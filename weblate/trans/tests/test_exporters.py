# -*- coding: utf-8 -*-
#
# Copyright © 2012 - 2016 Michal Čihař <michal@cihar.com>
#
# This file is part of Weblate <https://weblate.org/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from django.test import TestCase

from weblate.lang.models import Language
from weblate.trans.exporters import (
    PoExporter, PoXliffExporter, XliffExporter, TBXExporter, MoExporter, CSVExporter
)
from weblate.trans.models import (
    Dictionary, Project, SubProject, Translation, Unit,
)


class PoExporterTest(TestCase):
    _class = PoExporter
    _has_context = True

    def get_exporter(self, lang=None):
        if lang is None:
            lang = Language(code='xx')
        return self._class(
            language=lang,
            project=Project(slug='test', name='TEST'),
        )

    def check_export(self, exporter):
        output = exporter.serialize()
        self.assertIsNotNone(output)
        return output

    def check_plurals(self, result):
        self.assertIn(b'msgid_plural', result)
        self.assertIn(b'msgstr[2]', result)

    def check_dict(self, word):
        exporter = self.get_exporter()
        exporter.add_dictionary(word)
        self.check_export(exporter)

    def test_dictionary(self):
        self.check_dict(Dictionary(source='foo', target='bar'))

    def test_dictionary_markup(self):
        self.check_dict(Dictionary(source='<b>foo</b>', target='<b>bar</b>'))

    def test_dictionary_special(self):
        self.check_dict(Dictionary(source='bar\x1e\x1efoo', target='br\x1eff'))

    def check_unit(self, nplurals=3, **kwargs):
        if nplurals == 3:
            equation = 'n==0 ? 0 : n==1 ? 1 : 2'
        else:
            equation = '0'
        lang = Language(
            code='zz',
            nplurals=nplurals,
            pluralequation=equation
        )
        project = Project(
            slug='test',
            source_language=Language.objects.get(code='en'),
        )
        subproject = SubProject(slug='comp', project=project)
        unit = Unit(
            translation=Translation(
                language=lang,
                subproject=subproject
            ),
            **kwargs
        )
        exporter = self.get_exporter(lang)
        exporter.add_unit(unit)
        return self.check_export(exporter)

    def test_unit(self):
        self.check_unit(
            source='xxx',
            target='yyy',
        )

    def test_unit_plural(self):
        result = self.check_unit(
            source='xxx\x1e\x1efff',
            target='yyy\x1e\x1efff\x1e\x1ewww',
            translated=True,
        )
        self.check_plurals(result)

    def test_unit_plural_one(self):
        self.check_unit(
            nplurals=1,
            source='xxx\x1e\x1efff',
            target='yyy',
            translated=True,
        )

    def test_unit_not_translated(self):
        self.check_unit(
            nplurals=1,
            source='xxx\x1e\x1efff',
            target='yyy',
            translated=False,
        )

    def test_context(self):
        result = self.check_unit(
            source='foo',
            target='bar',
            context='context',
            translated=True,
        )
        if self._has_context:
            self.assertIn(b'context', result)
        elif self._has_context is not None:
            self.assertNotIn(b'context', result)


class PoXliffExporterTest(PoExporterTest):
    _class = PoXliffExporter
    _has_context = False

    def check_plurals(self, result):
        self.assertIn(b'[2]', result)


class XliffExporterTest(PoExporterTest):
    _class = XliffExporter
    _has_context = False

    def check_plurals(self, result):
        # Doesn't support plurals
        return


class TBXExporterTest(PoExporterTest):
    _class = TBXExporter
    _has_context = False

    def check_plurals(self, result):
        # Doesn't support plurals
        return


class MoExporterTest(PoExporterTest):
    _class = MoExporter
    _has_context = True

    def check_plurals(self, result):
        self.assertIn(b'www', result)


class CSVExporterTest(PoExporterTest):
    _class = CSVExporter
    _has_context = True

    def check_plurals(self, result):
        # Doesn't support plurals
        pass

    def setUp(self):
        self.exporter = self.get_exporter()

    def test_has_get_storage(self):
        self.assertTrue(hasattr(self.exporter, 'get_storage'))

    def test_has_setsourcelanguage(self):
        self.assertTrue(hasattr(self.exporter.storage, 'setsourcelanguage'))

    def test_has_settargetlanguage(self):
        self.assertTrue(hasattr(self.exporter.storage, 'settargetlanguage'))

    def test_has_UnitClass(self):
        self.assertTrue(hasattr(self.exporter.storage, 'UnitClass'))

    def test_has_addunit(self):
        self.assertTrue(hasattr(self.exporter.storage, 'addunit'))
