# -*- coding: utf-8 -*-

from b3j0f.utils.ut import UTCase
from unittest import main

from link.fulltext.filter import FulltextMatch


class TestMatcher(UTCase):
    def test_query(self):
        fm = FulltextMatch('a:(foo OR bar) b:(foo OR bar)')

        docs = [
            {'a': 'foo', 'b': 'foo'},
            {'a': 'foo', 'b': 'bar'},
            {'a': 'bar', 'b': 'foo'},
            {'a': 'bar', 'b': 'bar'}
        ]

        for doc in docs:
            self.assertTrue(fm(doc))

        docs = [
            {'a': 'foo'},
            {'b': 'bar'},
            {'c': 'baz'}
        ]

        for doc in docs:
            self.assertFalse(fm({'a': 'foo'}))


if __name__ == '__main__':
    main()
