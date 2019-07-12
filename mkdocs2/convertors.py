from mkdocs2.types import Convertor, File, Files, Env
import functools
import os
import shutil
import jinja2
import markdown
import typing
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from markdown.util import etree


class URLProcessor(Treeprocessor):
    def __init__(self, convert_url: typing.Callable[[str], str]) -> None:
        self.convert_url = convert_url

    def run(self, root: etree.ElementTree) -> etree.ElementTree:
        """
        Update urls on anchors and images to make them relative
        Iterates through the full document tree looking for specific
        tags and then makes them relative based on the site navigation
        """
        for element in root.iter():
            if element.tag == "a":
                url = element.get("href")
                url = self.convert_url(url)
                element.set("href", url)
            elif element.tag == "img":
                url = element.get("src")
                url = self.convert_url(url)
                element.set("src", url)

        return root


class TransformURLExtension(Extension):
    """
    The Extension class is what we pass to markdown, it then
    registers the Treeprocessor.
    """

    def __init__(self, convert_url: typing.Callable[[str], str]) -> None:
        self.convert_url = convert_url

    def extendMarkdown(self, md: markdown.Markdown) -> None:
        url_processor = URLProcessor(self.convert_url)
        md.treeprocessors.register(url_processor, "url", 10)


class MarkdownConvertor(Convertor):
    def __init__(self, config: dict) -> None:
        self.template_dir = config["build"]["template_dir"]
        loader = jinja2.FileSystemLoader(self.template_dir)
        self.env = jinja2.Environment(loader=loader)

    def get_output_path(self, input_path: str) -> str:
        output_path = os.path.splitext(input_path)[0]
        if os.path.basename(output_path) == "index":
            return output_path + ".html"
        return os.path.join(output_path, "index.html")

    def convert(self, file: File, env: Env) -> None:
        template = self.env.get_template("base.html")

        url = functools.partial(env.get_url, from_file=file)
        nav = env.nav
        nav_page = nav.lookup_page(file)

        md = markdown.Markdown(
            extensions=[TransformURLExtension(convert_url=url), "fenced_code"]
        )
        text = file.read_input_text()
        content = md.convert(text)
        html = template.render(content=content, url=url, nav=nav, nav_page=nav_page)
        file.write_output_text(html)


class StaticFileConvertor(Convertor):
    def __init__(self, config: dict) -> None:
        pass

    def get_output_path(self, input_path: str) -> str:
        return input_path

    def convert(self, file: File, env: Env) -> None:
        shutil.copy2(file.full_input_path, file.full_output_path)
