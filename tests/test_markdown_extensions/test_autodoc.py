from markdown import Markdown
from markdown.extensions.toc import TocExtension
from mkdocs2.markdown_extensions.autodoc import AutoDocExtension, trim_docstring, get_params
import inspect


def test_autodoc_function():
    md = Markdown(extensions=[AutoDocExtension()])
    text = md.convert(
        """
# API reference

This is an API reference.

::: import_examples.example_function
    :docstring:
""")
    assert text == """<h1>API reference</h1>
<p>This is an API reference.</p>
<div class="autodoc">
<p class="autodoc-signature"><code class="autodoc-module">import_examples.</code><code class="autodoc-name">example_function</code><span class="autodoc-punctuation">(</span><em class="autodoc-param">a</em><span class="autodoc-punctuation">, </span><em class="autodoc-param">b=None</em><span class="autodoc-punctuation">, </span><em class="autodoc-param">**kwargs</em><span class="autodoc-punctuation">)</span></p>
<div class="autodoc-docstring">
<p>This is my <em>docstring</em>.</p>
</div>
</div>"""


def test_autodoc_class():
    md = Markdown(extensions=[AutoDocExtension()])
    text = md.convert(
        """
# API reference

This is an API reference.

::: import_examples.ExampleClass
    :docstring:
""")
    assert text == """<h1>API reference</h1>
<p>This is an API reference.</p>
<div class="autodoc">
<p class="autodoc-signature"><em>class </em><code class="autodoc-module">import_examples.</code><code class="autodoc-name">ExampleClass</code><span class="autodoc-punctuation">(</span><em class="autodoc-param">b=None</em><span class="autodoc-punctuation">, </span><em class="autodoc-param">**kwargs</em><span class="autodoc-punctuation">)</span></p>
<div class="autodoc-docstring">
<p>This is my <em>docstring</em>.</p>
</div>
</div>"""


def test_autodoc_class_members():
    md = Markdown(extensions=[AutoDocExtension()])
    text = md.convert(
        """
# API reference

This is an API reference.

::: import_examples.ExampleClass
    :docstring:
    :members:
""")
    assert text == """<h1>API reference</h1>
<p>This is an API reference.</p>
<div class="autodoc">
<p class="autodoc-signature"><em>class </em><code class="autodoc-module">import_examples.</code><code class="autodoc-name">ExampleClass</code><span class="autodoc-punctuation">(</span><em class="autodoc-param">b=None</em><span class="autodoc-punctuation">, </span><em class="autodoc-param">**kwargs</em><span class="autodoc-punctuation">)</span></p>
<div class="autodoc-docstring">
<p>This is my <em>docstring</em>.</p>
</div>
<div class="autodoc-members">
<p class="autodoc-signature"><code class="autodoc-name">example_method</code><span class="autodoc-punctuation">(</span><em class="autodoc-param">self</em><span class="autodoc-punctuation">)</span></p>
<div class="autodoc-docstring">
<p>A method <em>docstring</em>.</p>
</div>
</div>
</div>"""


def test_autodoc_trailing_text():
    md = Markdown(extensions=[AutoDocExtension()])
    text = md.convert(
        """
::: import_examples.example_function
    :docstring:
Some trailing text.
""")
    assert text == """<div class="autodoc">
<p class="autodoc-signature"><code class="autodoc-module">import_examples.</code><code class="autodoc-name">example_function</code><span class="autodoc-punctuation">(</span><em class="autodoc-param">a</em><span class="autodoc-punctuation">, </span><em class="autodoc-param">b=None</em><span class="autodoc-punctuation">, </span><em class="autodoc-param">**kwargs</em><span class="autodoc-punctuation">)</span></p>
<div class="autodoc-docstring">
<p>This is my <em>docstring</em>.</p>
</div>
</div>
<p>Some trailing text.</p>"""


def test_trim_docstring():
    def test_no_docstring():
        pass  # pragma: nocover

    def test_singleline_docstring():
        """Single-line docstring"""
        pass  # pragma: nocover

    def test_multiline_docstring():
        """
        Multi-line
        docstring
        """
        pass  # pragma: nocover

    assert trim_docstring(test_no_docstring.__doc__) == ""
    assert trim_docstring(test_singleline_docstring.__doc__) == "Single-line docstring"
    assert trim_docstring(test_multiline_docstring.__doc__) == "Multi-line\ndocstring"


def test_get_params():
    def generics(*args, **kwargs):
        pass  # pragma: nocover

    def keyword_only(*, foo, bar):
        pass  # pragma: nocover


    assert get_params(inspect.signature(pow)) == ['/', 'x', 'y', 'z=None']
    assert get_params(inspect.signature(generics)) == ['*args', '**kwargs']
    assert get_params(inspect.signature(keyword_only)) == ['*', 'foo', 'bar']
