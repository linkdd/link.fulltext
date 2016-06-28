# -*- coding: utf-8 -*-

from link.middleware.core import Feature


class FulltextIndex(Feature):
    """
    API for middlewares supporting the Full-Text Index feature.
    """

    name = 'fulltext'

    def search(self, query):
        raise NotImplementedError()

    def add(self, doc):
        raise NotImplementedError()

    def delete(self, query):
        raise NotImplementedError()
