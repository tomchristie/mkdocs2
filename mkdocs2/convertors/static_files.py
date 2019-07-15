import shutil
import typing
from mkdocs2.types import Convertor, File, Env, TableOfContents


class StaticFiles(Convertor):
    def __init__(self, config: dict) -> None:
        pass

    def get_output_path(self, input_path: str) -> str:
        return input_path

    def build_toc(self, file: File, env: Env) -> typing.Optional[TableOfContents]:
        return None

    def convert(self, file: File, env: Env) -> None:
        shutil.copy2(file.full_input_path, file.full_output_path)
