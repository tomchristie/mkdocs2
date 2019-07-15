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
    def __init__(self, config: dict) -> None:
        self.template_dir = config["build"]["template_dir"]
        loader = jinja2.FileSystemLoader(self.template_dir)
        self.env = jinja2.Environment(loader=loader)

    def get_output_path(self, input_path: str) -> str:
        output_path = os.path.splitext(input_path)[0]
        if os.path.basename(output_path) == "index":
            return output_path + ".html"
        return os.path.join(output_path, "index.html")

    def build_toc(self, file: File, env: Env) -> typing.Optional[TableOfContents]:
        md = Markdown(extensions=[TocExtension()])
        text = file.read_input_text()
        content = md.convert(text)
        headers = self.tokens_to_headers(md.toc_tokens)
        return TableOfContents(headers)

    def tokens_to_headers(self, tokens: dict) -> typing.List[Header]:
        # See https://python-markdown.github.io/extensions/toc/
        return [
            Header(
                id=token["id"],
                name=token["name"],
                level=token["level"],
                children=self.tokens_to_headers(token["children"]),
            )
            for token in tokens
        ]

    def convert(self, file: File, env: Env) -> None:
        template = self.env.get_template("base.html")

        url = functools.partial(env.get_url, from_file=file)
        nav = env.nav
        current_page = nav.lookup_page(file)

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
        html = template.render(context)
        file.write_output_text(html)
