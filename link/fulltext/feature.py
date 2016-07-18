# -*- coding: utf-8 -*-

from link.feature import Feature


class FulltextIndex(Feature):
    """
    API for middlewares supporting the Full-Text Index feature.
    """

    name = 'fulltext'
    DATA_ID = 'id'

    def search(self, query):
        raise NotImplementedError()

    def add(self, doc):
        raise NotImplementedError()

    def delete(self, query):
        raise NotImplementedError()
