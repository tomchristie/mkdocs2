import typing
from markdown import Markdown
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


class ConvertURLs(Extension):
    """
    The Extension class is what we pass to markdown, it then
    registers the Treeprocessor.
    """

    def __init__(self, convert_url: typing.Callable[[str], str]) -> None:
        self.convert_url = convert_url

    def extendMarkdown(self, md: Markdown) -> None:
        url_processor = URLProcessor(self.convert_url)
        md.treeprocessors.register(url_processor, "url", 10)
