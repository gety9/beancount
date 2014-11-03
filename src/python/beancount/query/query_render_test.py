import datetime
import io
import re
import unittest
import textwrap
import functools
import collections

from beancount.core.amount import D
from beancount.core.amount import Decimal
from beancount.core.amount import ZERO
from beancount.core import inventory
from beancount.core import position
from beancount.query import query_render
from beancount.utils.misc_utils import box


class ColumnRendererBase(unittest.TestCase):

    RendererClass = None

    def get(self, *values):
        rdr = self.RendererClass()
        for value in values:
            rdr.update(value)
        rdr.prepare()
        return rdr


class TestStringRenderer(ColumnRendererBase):

    RendererClass = query_render.StringRenderer

    def test_simple(self):
        rdr = self.get('a', 'bb', 'ccc', '')
        self.assertEqual('dd ', rdr.format('dd'))
        self.assertEqual('   ', rdr.format(''))

    def test_nones(self):
        rdr = self.get(None, 'bb', 'ccc', None)
        self.assertEqual('dd ', rdr.format('dd'))
        self.assertEqual('   ', rdr.format(None))

    def test_overflow(self):
        rdr = self.get('a', 'bb', 'ccc', '')
        self.assertEqual('eee', rdr.format('eeee'))


class TestDateTimeRenderer(ColumnRendererBase):

    RendererClass = query_render.DateTimeRenderer

    def test_simple(self):
        rdr = self.get(datetime.date(2014, 11, 3))
        self.assertEqual('2014-10-03', rdr.format(datetime.date(2014, 10, 3)))

    def test_nones(self):
        rdr = self.get(None, datetime.date(2014, 11, 3), None)
        self.assertEqual('2014-03-30', rdr.format(datetime.date(2014, 3, 30)))
        self.assertEqual('          ', rdr.format(None))


class TestDecimalRenderer(ColumnRendererBase):

    RendererClass = query_render.DecimalRenderer

    def test_integers(self):
        rdr = self.get(D('1'), D('222'), D('33'))
        self.assertEqual('444', rdr.format(D('444')))

    def test_fractional(self):
        rdr = self.get(D('1.23'), D('1.2345'), D('2.345'))
        self.assertEqual('1.0000', rdr.format(D('1')))
        self.assertEqual('2.3457', rdr.format(D('2.34567890')))

    def test_mixed(self):
        rdr = self.get(D('1000'), D('0.12334'))
        self.assertEqual('   1.00000', rdr.format(D('1')))

    def test_zero_integers(self):
        rdr = self.get(D('0.1234'))
        self.assertEqual('1.0000', rdr.format(D('1')))

    def test_nones(self):
        rdr = self.get(None, D('0.1234'), None)
        self.assertEqual('1.0000', rdr.format(D('1')))
        self.assertEqual('      ', rdr.format(None))


class TestInventoryRenderer(ColumnRendererBase):

    RendererClass = query_render.InventoryRenderer

    def test_various(self):
        inv = inventory.from_string('100.00 USD')
        rdr = self.get(inv)
        self.assertEqual(['100.00 USD'],
                         rdr.format(inv))

        inv = inventory.from_string('5 GOOG {500.23 USD}')
        rdr = self.get(inv)
        self.assertEqual(['5 GOOG {500.23 USD}'],
                         rdr.format(inv))

        inv = inventory.from_string('5 GOOG {500.23 USD}, 12.3456 CAAD')
        rdr = self.get(inv)
        self.assertEqual([' 5.0000 GOOG {500.23 USD}',
                          '12.3456 CAAD             '],
                         rdr.format(inv))


class TestPositionRenderer(ColumnRendererBase):

    RendererClass = query_render.PositionRenderer

    def test_various(self):
        pos = position.from_string('100.00 USD')
        rdr = self.get(pos)
        self.assertEqual(['100.00 USD'],
                         rdr.format(pos))

        pos = position.from_string('5 GOOG {500.23 USD}')
        rdr = self.get(pos)
        self.assertEqual(['5 GOOG {500.23 USD}'],
                         rdr.format(pos))


class TestQueryRender(unittest.TestCase):

    def test_render_str(self):
        types = [('account', str)]
        Row = collections.namedtuple('TestRow', [name for name, type in types])
        rows = [
            Row('Assets:US:Babble:Vacation'),
            Row('Expenses:Vacation'),
            Row('Income:US:Babble:Vacation'),
        ]
        oss = io.StringIO()
        query_render.render_text(types, rows, oss)
        with box():
            print(oss.getvalue())

    def test_render_Decimal(self):
        types = [('number', Decimal)]
        Row = collections.namedtuple('TestRow', [name for name, type in types])
        rows = [
            Row(D('123.1')),
            Row(D('234.12')),
            Row(D('345.123')),
            Row(D('456.1234')),
        ]
        oss = io.StringIO()
        query_render.render_text(types, rows, oss)
        with box():
            print(oss.getvalue())
