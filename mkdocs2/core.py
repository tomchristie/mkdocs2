from mkdocs2 import convertors, types
from urllib.parse import urlparse, urlunparse, urljoin
import fnmatch
import os
import typing


def build(config: typing.Dict) -> None:
    base_url = config["site"].get("url")
    input_dir = config["build"]["input_dir"]
    output_dir = config["build"]["output_dir"]
    nav_info = config.get("nav", {})
    file_convertors = {}  # type: typing.Dict[str, convertors.Convertor]
    file_convertors["**.md"] = convertors.MarkdownConvertor(config)

    files = gather_files(
        input_dir=input_dir, output_dir=output_dir, file_convertors=file_convertors
    )
    nav = load_nav(nav_info, files, base_url)
    env = types.Env(files, nav, base_url, config)
    for file in files:
        dirname = os.path.dirname(file.full_output_path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        nav.activate(file)
        file.convertor.convert(file, env)
        nav.deactivate()


def gather_files(
    input_dir: str,
    output_dir: str,
    default_convertor: types.Convertor = None,
    file_convertors: typing.Dict[str, types.Convertor] = None,
    sub_dir: str = "",
) -> types.Files:
    """
    Determine all of the files in the input directory.
    """
    if default_convertor is None:
        default_convertor = convertors.StaticFileConvertor(config={})
    if file_convertors is None:
        file_convertors = {}

    files = types.Files()
    dirname = os.path.join(input_dir, sub_dir)
    for basename in sorted(os.listdir(dirname)):
        path = os.path.join(dirname, basename)
        if os.path.isdir(path):
            next_sub_dir = os.path.join(sub_dir, basename)
            files += gather_files(
                input_dir=input_dir,
                output_dir=output_dir,
                default_convertor=default_convertor,
                file_convertors=file_convertors,
                sub_dir=next_sub_dir,
            )
        else:
            input_path = os.path.join(sub_dir, basename)
            convertor = default_convertor
            for pattern, file_convertor in file_convertors.items():
                if fnmatch.fnmatch(input_path, pattern):
                    convertor = file_convertor
                    break
            output_path = convertor.get_output_path(input_path)
            file = types.File(
                input_path=input_path,
                output_path=output_path,
                input_dir=input_dir,
                output_dir=output_dir,
                convertor=convertor,
            )
            files.append(file)
    return files


def load_nav(nav_info: dict, files: types.Files, base_url: str = None) -> types.Nav:
    """
    Determine the navigation info.
    """
    nav_items = load_nav_items(nav_info=nav_info, files=files)
    return types.Nav(nav_items, base_url=base_url)


def load_nav_items(
    nav_info: dict, files: types.Files
) -> typing.List[typing.Union[types.NavGroup, types.NavPage]]:
    nav_items = []  # type: typing.List[typing.Union[types.NavGroup, types.NavPage]]
    for title, child in nav_info.items():
        if isinstance(child, str):
            file = files.get_by_input_path(child)
            nav_page = types.NavPage(title=title, file=file)
            nav_items.append(nav_page)
        else:
            children = load_nav_items(child, files)
            nav_group = types.NavGroup(title=title, children=children)
            nav_items.append(nav_group)
    return nav_items
