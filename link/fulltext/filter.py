# -*- coding: utf-8 -*-

from b3j0f.utils.runtime import singleton_per_scope
from b3j0f.utils.iterable import isiterable

from grako.model import DepthFirstWalker, ModelBuilderSemantics
from link.utils.grammar import codegenerator


FULLTEXT_GRAMMAR = '''
@@keyword :: OR AND TO

sign = "+" | "-" ;
digit = /[0-9]/ ;
number::NumberNode = [ sign:sign ] value:({ digit }+) ;

@name
literal::LiteralNode = value:(/\w*/) ;

@name
identifier::IdentifierNode = name:literal ;

boundary::BoundaryNode = value:("*" | number) ;
range::RangeNode = "[" begin:boundary "TO" end:boundary "]" ;

group::GroupNode = "(" s:search ")" ;
expr::ExpressionNode = value:(group | range | literal) ;
term::TermNode = [ inverted:"-" ] [ field:identifier ":" ] pattern:expr ;

or::OrNode = left:(search | term) "OR" right:(term | search) ;
and::AndNode = left:(search | term) [ "AND" ] right:(term | search) ;

search::SearchNode = v:(and | or | term) ;

start::RootNode = search:search ;
'''

fulltext_parser_module = singleton_per_scope(
    lambda: codegenerator('fulltext_parser', 'Fulltext', FULLTEXT_GRAMMAR)
)

fulltext_parser = singleton_per_scope(
    fulltext_parser_module.FulltextParser,
    semantics=ModelBuilderSemantics()
)


class FulltextWalker(DepthFirstWalker):
    def __init__(self, context, *args, **kwargs):
        super(FulltextWalker, self).__init__(*args, **kwargs)

        self.context = context

    def check_field(self, field, pattern):
        result = False
        pattern = pattern.value

        if pattern.__class__.__name__ == 'LiteralNode':
            if isiterable(self.context[field]):
                result = pattern.value in self.context[field]

            else:
                result = pattern.value == self.context[field]

        elif pattern.__class__.__name__ == 'RangeNode':
            begin, end = pattern.value
            local_result = True

            if begin is not None:
                local_result = self.context[field] >= begin

            if local_result and end is not None:
                local_result = self.context[field] < end

            result = local_result

        elif pattern.__class__.__name__ == 'GroupNode':
            pass

        return result

    def walk_IdentifierNode(self, node, child_retval):
        node.name = node.name.value

    def walk_NumberNode(self, node, child_retval):
        n = ''.join(node.value)

        if node.sign is not None:
            n = int('{0}{1}'.format(node.sign, n))

        else:
            n = int(n)

        node.value = n
        del node.sign

    def walk_RangeNode(self, node, child_retval):
        begin = None if node.begin.value == "*" else node.begin.value.value
        end = None if node.end.value == "*" else node.end.value.value

        node.value = (begin, end)
        del node.begin
        del node.end

    def walk_TermNode(self, node, child_retval):
        node.inverted = node.inverted is not None

        if node.field is not None:
            node.field = node.field.name

        result = False

        if node.field is not None and node.field in self.context:
            result = self.check_field(node.field, node.pattern)

        elif node.field is None:
            for field in self.context.keys():
                local_result = self.check_field(field, node.pattern)

                if local_result:
                    result = True
                    break

        if node.inverted:
            result = not result

        return result

    def walk_OrNode(self, node, child_retval):
        return any(child_retval)

    def walk_AndNode(self, node, child_retval):
        return all(child_retval)

    def walk_SearchNode(self, node, child_retval):
        return child_retval[0]

    def walk_RootNode(self, node, child_retval):
        print(node)
        return child_retval[0]


class FulltextMatch(object):
    def __init__(self, query, *args, **kwargs):
        super(FulltextMatch, self).__init__(*args, **kwargs)

        self.model = fulltext_parser.parse(query)

    def __call__(self, document):
        walker = FulltextWalker(document)
        return walker.walk(self.model)
