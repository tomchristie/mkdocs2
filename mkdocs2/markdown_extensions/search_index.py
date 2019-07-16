from markdown import Markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from markdown.util import etree


class SearchIndexProcessor(Treeprocessor):
    def run(self, root: etree.ElementTree) -> etree.ElementTree:
        search_index = []

        for element in root.iter():
            if element.tag in {"h1", "h2", "h3", "h4", "h5"} and element.get("id"):
                search_index.append(
                    {"ref": element.get("id"), "title": element.text, "text": ""}
                )
            elif search_index:
                search_index[-1]["text"] += element.text + " "

        self.md.search_index = search_index


class SearchIndex(Extension):
    def extendMarkdown(self, md: Markdown) -> None:
        processor = SearchIndexProcessor(md)
        md.treeprocessors.register(processor, "search_index", 1)
