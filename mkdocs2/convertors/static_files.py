import shutil
import typing
from mkdocs2.types import Convertor, File, Env, TableOfContents


class StaticFiles(Convertor):
    def should_handle_file(self, input_path: str) -> bool:
        return True

    def get_output_path(self, input_path: str) -> str:
        return input_path

    def get_extra_paths(self) -> typing.List[str]:
        return []

    def build_toc(self, file: File, env: Env) -> typing.Optional[TableOfContents]:
        return None

    def convert(self, file: File, env: Env) -> None:
        shutil.copy2(file.full_input_path, file.full_output_path)
