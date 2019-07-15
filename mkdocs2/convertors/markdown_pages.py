from mkdocs2.types import Convertor, File, Files, TableOfContents, Header, Env
import functools
import os
import jinja2
import typing
from markdown import Markdown
from markdown.extensions.toc import TocExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from mkdocs2.markdown_extensions.convert_urls import ConvertURLs


class MarkdownPages(Convertor):
    patterns = ["**.md"]

    def get_output_path(self, input_path: str) -> str:
        output_path = os.path.splitext(input_path)[0]
        if os.path.basename(output_path) == "index":
            return output_path + ".html"
        return os.path.join(output_path, "index.html")

    def build_toc(self, file: File, env: Env) -> typing.Optional[TableOfContents]:
        # See https://python-markdown.github.io/extensions/toc/

        def get_headers(toc_tokens: typing.List[dict]) -> typing.List[Header]:
            return [
                Header(
                    id=token["id"],
                    name=token["name"],
                    level=token["level"],
                    children=get_headers(token["children"]),
                )
                for token in toc_tokens
            ]

        md = Markdown(extensions=[TocExtension()])
        text = file.read_input_text()
        content = md.convert(text)
        headers = get_headers(md.toc_tokens)
        return TableOfContents(headers)

    def convert(self, file: File, env: Env) -> None:
        url = functools.partial(env.get_url, from_file=file)
        current_page = env.nav.lookup_page(file)
        nav = env.nav

        md = Markdown(
            extensions=[
                TocExtension(permalink=True),
                FencedCodeExtension(),
                ConvertURLs(convert_url=url),
            ]
        )
        text = file.read_input_text()
        content = md.convert(text)
        context = {
            "content": content,
            "url": url,
            "nav": nav,
            "current_page": current_page,
            "toc": file.toc,
        }
        html = env.render_template("base.html", context)
        file.write_output_text(html)
