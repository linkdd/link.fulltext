# -*- coding: utf-8 -*-

from b3j0f.utils.runtime import singleton_per_scope

from link.utils.grammar import codegenerator, adopt_children, find_ancestor
from grako.model import DepthFirstWalker, ModelBuilderSemantics


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

or::OrNode = left:(search | term) "OR" right:(term | search)
           | ("(" left:(search | term) "OR" right:(term | search) ")");
and::AndNode = left:(search | term) [ "AND" ] right:(term | search)
             | ("(" left:(search | term) [ "AND" ] right:(term | search) ")") ;

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

    _IDENTIFIER_NODE = '__identifier__'

    def __init__(self, context, *args, **kwargs):
        super(FulltextWalker, self).__init__(*args, **kwargs)

        self.context = context

    def check_field(self, field, pattern):
        exprtype = pattern.value.__class__.__name__
        result = True

        if field not in self.context:
            result = False

        elif exprtype == 'LiteralNode':
            result = pattern.value.value in self.context[field]

        elif exprtype == 'RangeNode':
            begin, end = pattern.value.value

            if begin is not None:
                result = self.context[field] > begin

            if end is not None:
                result = self.context[field] <= end

        return result

    def walk_IdentifierNode(self, node, child_retval):
        return FulltextWalker._IDENTIFIER_NODE

    def walk_TermNode(self, node, child_retval):
        result = False
        field = node.field

        # check if an expression was already evaluated
        child_retval = [
            retval
            for retval in child_retval
            if retval != FulltextWalker._IDENTIFIER_NODE
        ]

        if child_retval[0] is not None:
            result = child_retval[0]

        else:
            # find current field
            if field is None:
                parent = find_ancestor(node, 'TermNode')

                while parent is not None:
                    if parent.field is not None:
                        break

                    parent = find_ancestor(parent, 'TermNode')

                if parent is not None:
                    field = parent.field

            # no current field
            if field is None:
                for key in self.context.keys():
                    if self.check_field(key, node.pattern):
                        result = True
                        break

            else:
                result = self.check_field(field, node.pattern)

        if node.inverted:
            result = not result

        return result

    def walk_ExpressionNode(self, node, child_retval):
        exprtype = node.value.__class__.__name__

        return child_retval[0] if exprtype == 'GroupNode' else None

    def walk_OrNode(self, node, child_retval):
        return any(child_retval)

    def walk_AndNode(self, node, child_retval):
        return all(child_retval)

    def walk_GroupNode(self, node, child_retval):
        return child_retval[0]

    def walk_SearchNode(self, node, child_retval):
        return child_retval[0]

    def walk_RootNode(self, node, child_retval):
        return child_retval[0]


class _TreeSimplifier(DepthFirstWalker):
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

    def walk_RootNode(self, node, child_retval):
        return node


class FulltextMatch(object):
    def __init__(self, query, *args, **kwargs):
        super(FulltextMatch, self).__init__(*args, **kwargs)

        model = fulltext_parser.parse(query)
        simplifier = _TreeSimplifier()
        self.model = simplifier.walk(model)
        adopt_children(self.model._ast, parent=self.model)

    def __call__(self, document):
        walker = FulltextWalker(document)
        return walker.walk(self.model)
