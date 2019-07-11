from mkdocs2 import convertors, types
from urllib.parse import urlparse, urlunparse, urljoin
import fnmatch
import os
import posixpath
import typing


def build(config: typing.Dict) -> None:
    input_dir = config["build"]["input_dir"]
    output_dir = config["build"]["output_dir"]
    nav_info = config.get("nav", {})
    file_convertors = {}  # type: typing.Dict[str, convertors.Convertor]
    file_convertors["**.md"] = convertors.MarkdownConvertor(config)

    files = gather_files(
        input_dir=input_dir, output_dir=output_dir, file_convertors=file_convertors
    )
    nav = load_nav(nav_info, files)
    env = types.Env(files, nav, config)
    for file in files:
        dirname = os.path.dirname(file.full_output_path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        file.convertor.convert(file, env)


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


def load_nav(nav_info: dict, files: types.Files) -> types.Nav:
    """
    Determine the navigation info.
    """
    nav_items = []  # type: typing.List[typing.Union[types.NavGroup, types.NavPage]]
    for title, child in nav_info.items():
        if isinstance(child, str):
            file = files.get_by_input_path(child)
            nav_page = types.NavPage(title=title, file=file)
            nav_items.append(nav_page)
        else:
            child_nav = load_nav(child, files)
            nav_group = types.NavGroup(title=title, children=child_nav.items)
            nav_items.append(nav_group)
    return types.Nav(nav_items)


def url_function_for_file(
    from_file: types.File, files: types.Files, base_url: str = None
) -> typing.Callable[[str], str]:
    """
    Returns a `url()` function to use for converting any URLs in the given file.
    """

    def url(hyperlink: str) -> str:
        scheme, netloc, path, params, query, fragment = urlparse(hyperlink)
        if scheme or netloc or not path:
            return hyperlink

        if path.startswith("/"):
            # Path-absolute URLs are treated as-is.
            files.get_by_url_path(path)
            url = path
        else:
            # Path-relative URLs are treated as links to files.
            # We resolve which file is being referenced in order to determine
            # what the URL should be.
            path = path.replace("/", os.path.sep)
            path = os.path.join(os.path.dirname(from_file.input_path), path)
            path = os.path.normpath(path)
            file = files.get_by_input_path(path)
            url = file.url

        if base_url is None:
            path = posixpath.relpath(url, from_file.url)
            if url.endswith("/") and not path.endswith("/"):
                path += "/"
        else:
            scheme, netloc, path, _, _, _ = urlparse(urljoin(base_url, url))

        return urlunparse((scheme, netloc, path, params, query, fragment))

    return url
