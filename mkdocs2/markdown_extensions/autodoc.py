from markdown import Markdown
from markdown.extensions import Extension
from markdown.blockprocessors import BlockProcessor
from markdown.util import etree
from mkdocs2.core import import_from_string
import inspect
import re
import typing


# Fuzzy regex for determining source lines in __init__ that look like
# attribute assignments.  Eg. `self.counter = 0`
SET_ATTRIBUTE = re.compile('^([ \t]*)self[.]([A-Za-z0-9_]+) *=')


def get_params(signature: inspect.Signature) -> typing.List[str]:
    """
    Given a function signature, return a list of parameter strings
    to use in documentation.

    Eg. test(a, b=None, **kwargs) -> ['a', 'b=None', '**kwargs']
    """
    params = []
    render_pos_only_separator = True
    render_kw_only_separator = True

    for parameter in signature.parameters.values():
        value = parameter.name
        if parameter.default is not parameter.empty:
            value = f'{value}={parameter.default!r}'

        if parameter.kind is parameter.VAR_POSITIONAL:
            render_kw_only_separator = False
            value = f'*{value}'
        elif parameter.kind is parameter.VAR_KEYWORD:
            value = f'**{value}'
        elif parameter.kind is parameter.POSITIONAL_ONLY:
            if render_pos_only_separator:
                render_pos_only_separator = False
                params.append('/')
        elif parameter.kind is parameter.KEYWORD_ONLY:
            if render_kw_only_separator:
                render_kw_only_separator = False
                params.append('*')
        params.append(value)

    return params


def last_iter(seq: typing.Sequence) -> typing.Iterator:
    """
    Given an sequence, return a two-tuple (item, is_last) iterable.

    See: https://stackoverflow.com/a/1633483/596689
    """
    it = iter(seq)
    item = next(it)
    is_last = False

    for next_item in it:
        yield item, is_last
        item = next_item

    is_last = True
    yield item, is_last


def trim_docstring(docstring: typing.Optional[str]) -> str:
    """
    Trim leading indent from a docstring.

    See: https://www.python.org/dev/peps/pep-0257/#handling-docstring-indentation
    """
    if not docstring:
        return ''

    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = 1000
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))

    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < 1000:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())

    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)

    # Return a single string:
    return '\n'.join(trimmed)


# def guess_instance_attributes(cls: type) -> typing.Dict[str, str]:
#     """
#     Given a class, return a dictionary of {attribute_name: comment}, based
#     on the source code in the __init__ method.
#     """
#     instance_attributes = {}
#     source_lines, line_no = inspect.getsourcelines(getattr(cls, '__init__'))
#     for idx, line in enumerate(source_lines):
#         m = SET_ATTRIBUTE.match(line)
#         if not m:
#             continue
#
#         whitespace, name = m.group(1), m.group(2)
#         if name in instance_attributes:
#             continue
#
#         comment_lines = []
#         for potential in reversed(source_lines[:idx]):
#             if potential.startswith(whitespace + '# '):
#                 comment_lines.insert(0, potential[len(whitespace) + 2:])
#             else:
#                 break
#         instance_attributes[name] = ''.join(comment_lines)
#
#     return instance_attributes


class AutoDocProcessor(BlockProcessor):

    CLASSNAME = 'autodoc'
    RE = re.compile(r'(?:^|\n)::: ?([:a-zA-Z0-9_.]*) *(?:\n|$)')
    RE_SPACES = re.compile('  +')

    def test(self, parent: etree.Element, block: etree.Element) -> bool:
        sibling = self.lastChild(parent)
        return bool(self.RE.search(block) or \
            (block.startswith(' ' * self.tab_length) and sibling is not None and
             sibling.get('class', '').find(self.CLASSNAME) != -1))

    def run(self, parent: etree.Element, blocks: etree.Element) -> None:
        sibling = self.lastChild(parent)
        block = blocks.pop(0)
        m = self.RE.search(block)

        if m:
            block = block[m.end():]  # removes the first line

        block, theRest = self.detab(block)

        if m:
            import_string = m.group(1)
            item = import_from_string(import_string)

            autodoc_div = etree.SubElement(parent, 'div')
            autodoc_div.set('class', self.CLASSNAME)

            self.render_signature(autodoc_div, item, import_string)
            for line in block.splitlines():
                if line.startswith(":docstring:"):
                    docstring = trim_docstring(item.__doc__)
                    self.render_docstring(autodoc_div, item, docstring)
                elif line.startswith(":members:"):
                    self.render_members(autodoc_div, item)

        #else:
        #    self.parser.parseChunk(sibling, block)

        if theRest:
            # This block contained unindented line(s) after the first indented
            # line. Insert these lines as the first block of the master blocks
            # list for future processing.
            blocks.insert(0, theRest)

    def render_signature(self, elem: etree.Element, item: typing.Any, import_string: str) -> None:
        module_string, _, name_string = import_string.rpartition('.')
        signature = inspect.signature(item)

        # Eg: `some_module.attribute_name`
        signature_elem = etree.SubElement(elem, 'p')
        signature_elem.set('class', 'autodoc-signature')

        if inspect.isclass(item):
            qualifier_elem = etree.SubElement(signature_elem, 'em')
            qualifier_elem.text = "class "

        if module_string:
            module_elem = etree.SubElement(signature_elem, 'code')
            module_elem.text = module_string + '.'
            module_elem.set('class', 'autodoc-module')
        name_elem = etree.SubElement(signature_elem, 'code')
        name_elem.text = name_string
        name_elem.set('class', 'autodoc-name')

        # Eg: `(a, b='default', **kwargs)``
        bracket_elem = etree.SubElement(signature_elem, 'span')
        bracket_elem.text = '('
        bracket_elem.set('class', 'autodoc-punctuation')

        for param, is_last in last_iter(get_params(signature)):
            param_elem = etree.SubElement(signature_elem, 'em')
            param_elem.text = param
            param_elem.set('class', 'autodoc-param')

            if not is_last:
                comma_elem = etree.SubElement(signature_elem, 'span')
                comma_elem.text = ', '
                comma_elem.set('class', 'autodoc-punctuation')

        bracket_elem = etree.SubElement(signature_elem, 'span')
        bracket_elem.text = ')'
        bracket_elem.set('class', 'autodoc-punctuation')

    def render_docstring(self, elem: etree.Element, item: typing.Any, docstring: str) -> None:
        docstring_elem = etree.SubElement(elem, 'div')
        docstring_elem.set('class', 'autodoc-docstring')
        self.parser.parseChunk(docstring_elem, docstring)

    def render_members(self, elem: etree.Element, item: typing.Any) -> None:
        members_elem = etree.SubElement(elem, 'div')
        members_elem.set('class', 'autodoc-members')

        members = {}

        for attribute_name in dir(item):
            if not attribute_name.startswith('_'):
                attribute = getattr(item, attribute_name)
                if hasattr(attribute, '__doc__'):
                    members[attribute_name] = trim_docstring(attribute.__doc__)

        # if inspect.isclass(item):
        #    for attribute_name, comment in guess_instance_attributes(item).items():
        #        if attribute_name not in members:
        #            members[attribute_name] = comment

        for attribute_name, docs in members.items():
            attribute = getattr(item, attribute_name)
            self.render_signature(members_elem, attribute, attribute_name)
            self.render_docstring(members_elem, attribute, docs)



class AutoDocExtension(Extension):
    def extendMarkdown(self, md: Markdown) -> None:
        md.registerExtension(self)
        md.parser.blockprocessors.register(AutoDocProcessor(md.parser), 'autodoc', 110)
