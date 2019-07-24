from markdown import Markdown
from markdown.extensions import Extension
from markdown.blockprocessors import BlockProcessor
from markdown.util import etree
from mkdocs2.core import import_from_string
import inspect
import re
import typing


class AutoDocProcessor(BlockProcessor):

    CLASSNAME = 'autodoc'
    RE = re.compile(r'(?:^|\n)::: ?([:a-zA-Z0-9_.]*) *(?:\n|$)')
    RE_SPACES = re.compile('  +')

    def test(self, parent, block):
        sibling = self.lastChild(parent)
        return self.RE.search(block) or \
            (block.startswith(' ' * self.tab_length) and sibling is not None and
             sibling.get('class', '').find(self.CLASSNAME) != -1)

    def run(self, parent, blocks):
        sibling = self.lastChild(parent)
        block = blocks.pop(0)
        m = self.RE.search(block)

        if m:
            block = block[m.end():]  # removes the first line

        block, theRest = self.detab(block)

        if m:
            full_string = m.group(1)
            import_string, _, name_string = full_string.partition(':')
            attribute = import_from_string(full_string)
            attribute_signature = inspect.signature(attribute)

            autodoc_div = etree.SubElement(parent, 'div')
            autodoc_div.set('class', self.CLASSNAME)

            # Eg: `some_module.attribute_name`
            headline_elem = etree.SubElement(autodoc_div, 'p')
            import_elem = etree.SubElement(headline_elem, 'code')
            import_elem.text = import_string + '.'
            import_elem.set('class', 'autodoc-import')
            name_elem = etree.SubElement(headline_elem, 'code')
            name_elem.text = name_string
            name_elem.set('class', 'autodoc-name')

            # Eg: `(a, b='default', **kwargs)``
            bracket_elem = etree.SubElement(headline_elem, 'span')
            bracket_elem.text = '('
            bracket_elem.set('class', 'autodoc-punctuation')

            for param, is_last in self.last_iter(self.get_params(attribute_signature)):
                param_elem = etree.SubElement(headline_elem, 'em')
                param_elem.text = param
                param_elem.set('class', 'autodoc-param')

                if not is_last:
                    comma_elem = etree.SubElement(headline_elem, 'span')
                    comma_elem.text = ', '
                    comma_elem.set('class', 'autodoc-punctuation')

            bracket_elem = etree.SubElement(headline_elem, 'span')
            bracket_elem.text = ')'
            bracket_elem.set('class', 'autodoc-punctuation')

            # Render docstring
            docstring_elem = etree.SubElement(autodoc_div, 'div')
            docstring_elem.set('class', 'autodoc-docstring')

            docstring = self.trim(attribute.__doc__)
            self.parser.parseChunk(docstring_elem, docstring)

        else:
            self.parser.parseChunk(sibling, block)

        if theRest:
            # This block contained unindented line(s) after the first indented
            # line. Insert these lines as the first block of the master blocks
            # list for future processing.
            blocks.insert(0, theRest)

    def get_params(self, signature: inspect.Signature) -> typing.List[str]:
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

    def last_iter(self, it: typing.Iterator) -> typing.Iterator:
        """
        Given an iteratable, return a two-tuple (item, is_last) iterable.

        See: https://stackoverflow.com/a/1633483/596689
        """
        it = iter(it)
        item = next(it)
        is_last = False

        for next_item in it:
            yield item, is_last
            item = next_item

        is_last = True
        yield item, is_last

    def trim(self, docstring: typing.Optional[str]) -> str:
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


class AutoDocExtension(Extension):
    def extendMarkdown(self, md: Markdown) -> None:
        md.registerExtension(self)
        md.parser.blockprocessors.register(AutoDocProcessor(md.parser), 'autodoc', 110)
