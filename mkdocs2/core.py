from mkdocs2 import types
from urllib.parse import urlparse, urlunparse, urljoin
import fnmatch
import importlib
import os
import typing


def build(config: typing.Dict) -> None:
    base_url = config["build"].get("url")
    input_dir = config["build"]["input_dir"]
    output_dir = config["build"]["output_dir"]
    template_dir = config["build"]["template_dir"]
    nav_info = config.get("nav", {})

    convertors = []
    for convertor_info in config["convertors"]:
        cls = import_from_string(convertor_info)
        assert issubclass(cls, types.Convertor)
        convertors.append(cls())

    files = gather_files(
        input_dir=input_dir, output_dir=output_dir, convertors=convertors
    )
    nav = load_nav(nav_info, files, base_url)
    env = types.Env(files, nav, template_dir, base_url, config=config)
    for file in files:
        file.toc = file.convertor.build_toc(file, env)

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
    convertors: typing.List[types.Convertor],
    sub_dir: str = "",
) -> types.Files:
    """
    Determine all of the files in the input directory.
    """

    files = types.Files()
    dirname = os.path.join(input_dir, sub_dir)
    for basename in sorted(os.listdir(dirname)):
        path = os.path.join(dirname, basename)
        if os.path.isdir(path):
            # Descend into sub-directories.
            next_sub_dir = os.path.join(sub_dir, basename)
            files += gather_files(
                input_dir=input_dir,
                output_dir=output_dir,
                convertors=convertors,
                sub_dir=next_sub_dir,
            )
        else:
            #  Determine if there are any convertors that handle the given file.
            input_path = os.path.join(sub_dir, basename)
            for convertor in convertors:
                if convertor.should_handle_file(input_path):
                    output_path = convertor.get_output_path(input_path)
                    file = types.File(
                        input_path=input_path,
                        output_path=output_path,
                        input_dir=input_dir,
                        output_dir=output_dir,
                        convertor=convertor,
                    )
                    files.append(file)
                    break

    # Add any extra files that are provided by a convertor class.
    for convertor in convertors:
        for path in convertor.get_extra_paths():
            file = types.File(
                input_path="",
                output_path=path,
                input_dir="",
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


def import_from_string(import_str: str) -> typing.Any:
    module_str, _, attrs_str = import_str.partition(":")

    try:
        lookup = importlib.import_module(module_str)
    except ImportError as exc:
        raise ValueError(f"Could not import module {module_str!r}.")

    try:
        for attr in attrs_str.split("."):
            lookup = getattr(lookup, attr)
    except AttributeError as exc:
        raise ValueError(f"Attribute {attrs_str!r} not found in module {module_str!r}.")

    return lookup
