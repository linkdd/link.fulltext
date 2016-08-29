# -*- coding: utf-8 -*-

from b3j0f.utils.ut import UTCase
from unittest import main

from link.fulltext.filter import FulltextMatch


class TestMatcher(UTCase):
    def test_single(self):
        fm = FulltextMatch('a:foo')
        self.assertTrue(fm({'a': 'foo'}))
        self.assertFalse(fm({'a': 'bar'}))

    def test_inverted(self):
        fm = FulltextMatch('-a:foo')
        self.assertTrue(fm({'a': 'bar'}))
        self.assertFalse(fm({'a': 'foo'}))

    def test_range(self):
        fm = FulltextMatch('a:[5 TO 19]')

        docs = [
            {'a': i}
            for i in range(5, 20)
        ]

        for doc in docs:
            self.assertTrue(fm(doc))

        self.assertFalse(fm({'a': 4}))

        fm = FulltextMatch('a:[-10 TO *]')

        docs = [
            {'a': i}
            for i in range(-10, 10)
        ]

        for doc in docs:
            self.assertTrue(fm(doc))

        self.assertFalse(fm({'a': -11}))

    def test_complex_pattern(self):
        fm = FulltextMatch('a:(foo OR bar) b:(foo OR (bar AND baz))')

        docs = [
            {'a': 'foo', 'b': 'foo'},
            {'a': 'foo', 'b': 'barbaz'},
            {'a': 'bar', 'b': 'foo'},
            {'a': 'bar', 'b': 'bazbar'}
        ]

        for doc in docs:
            self.assertTrue(fm(doc))

        docs = [
            {'a': 'foo'},
            {'b': 'bar'},
            {'c': 'baz'}
        ]

        for doc in docs:
            self.assertFalse(fm(doc))

    def test_complex_query(self):
        fm = FulltextMatch('a:foo (b:bar OR (c:baz AND b:biz))')

        docs = [
            {'a': 'foo', 'b': 'bar'},
            {'a': 'foo', 'c': 'baz', 'b': 'biz'}
        ]

        for doc in docs:
            self.assertTrue(fm(doc))

        docs = [
            {'a': 'foo', 'b': 'baz'},
            {'a': 'foo', 'c': 'bar'},
            {'a': 'foo', 'c': 'baz', 'b': 'buz'}
        ]

        for doc in docs:
            self.assertFalse(fm(doc))

    def test_no_field(self):
        fm = FulltextMatch('foo OR bar')

        docs = [
            {'a': 'foo'},
            {'b': 'foo'},
            {'c': 'bar'}
        ]

        for doc in docs:
            self.assertTrue(fm(doc))

        self.assertFalse(fm({'a': 'baz'}))


if __name__ == '__main__':
    main()
