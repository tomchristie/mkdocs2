import typing
from mkdocs2.types import Convertor, File, Env, TableOfContents
from pygments.formatters import HtmlFormatter


class CodeHighlight(Convertor):
    def __init__(self, style: str='friendly', path: str='css/highlight.css'):
        self.style = style
        self.path = path

    def should_handle_file(self, input_path: str) -> bool:
        return False

    def get_extra_paths(self) -> typing.List[str]:
        return [self.path]

    def build_toc(self, file: File, env: Env) -> typing.Optional[TableOfContents]:
        return None

    def convert(self, file: File, env: Env) -> None:
        css = HtmlFormatter(style=self.style).get_style_defs()
        file.write_output_text(css)
