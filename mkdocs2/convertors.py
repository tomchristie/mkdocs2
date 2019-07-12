from mkdocs2.types import Convertor, File, Env
import os
import shutil
import jinja2
import markdown
import typing
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from markdown.util import etree


class URLProcessor(Treeprocessor):
    def __init__(self, url_func: typing.Callable[[str], str]) -> None:
        self.url_func = url_func

    def run(self, root: etree.ElementTree) -> etree.ElementTree:
        """
        Update urls on anchors and images to make them relative
        Iterates through the full document tree looking for specific
        tags and then makes them relative based on the site navigation
        """
        for element in root.iter():
            if element.tag == "a":
                url = element.get("href")
                url = self.url_func(url)
                element.set("href", url)
            elif element.tag == "img":
                url = element.get("src")
                url = self.url_func(url)
                element.set("src", url)

        return root


class TransformURLExtension(Extension):
    """
    The Extension class is what we pass to markdown, it then
    registers the Treeprocessor.
    """

    def __init__(self, url_func: typing.Callable[[str], str]) -> None:
        self.url_func = url_func

    def extendMarkdown(self, md: markdown.Markdown) -> None:
        url_processor = URLProcessor(self.url_func)
        md.treeprocessors.register(url_processor, "url", 10)


class MarkdownConvertor(Convertor):
    def __init__(self, config: dict) -> None:
        self.base_url = config["site"]["url"]
        self.template_dir = config["build"]["template_dir"]
        loader = jinja2.FileSystemLoader(self.template_dir)
        self.env = jinja2.Environment(loader=loader)

    def get_output_path(self, input_path: str) -> str:
        output_path = os.path.splitext(input_path)[0]
        if os.path.basename(output_path) == "index":
            return output_path + ".html"
        return os.path.join(output_path, "index.html")

    def convert(self, file: File, env: Env) -> None:
        from mkdocs2.core import url_function_for_file

        url_func = url_function_for_file(file, env.files, base_url=self.base_url)
        md = markdown.Markdown(
            extensions=[TransformURLExtension(url_func=url_func), "fenced_code"]
        )

        template = self.env.get_template("base.html")
        text = file.read_input_text()
        content = md.convert(text)
        nav = env.nav
        nav_page = nav.lookup_page(file)
        html = template.render(
            content=content, url=url_func, nav=nav, nav_page=nav_page
        )
        file.write_output_text(html)


class StaticFileConvertor(Convertor):
    def __init__(self, config: dict) -> None:
        pass

    def get_output_path(self, input_path: str) -> str:
        return input_path

    def convert(self, file: File, env: Env) -> None:
        shutil.copy2(file.full_input_path, file.full_output_path)
