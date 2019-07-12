import os
import posixpath
import typing
from urllib.parse import urlparse, urlunparse, urljoin


class Convertor:
    """
    Responsible for converting the source input file to the built output file.
    """

    def __init__(self, config: dict) -> None:
        pass  # pragma: no cover

    def get_output_path(self, input_path: str) -> str:
        raise NotImplementedError()  # pragma: no cover

    def convert(self, file: "File", env: "Env") -> None:
        raise NotImplementedError()  # pragma: no cover


class File:
    """
    A single file that needs to be built.
    """

    def __init__(
        self,
        input_path: str,
        output_path: str,
        input_dir: str,
        output_dir: str,
        convertor: Convertor,
    ) -> None:
        self.input_path = input_path
        self.output_path = output_path
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.convertor = convertor

    def __eq__(self, other: typing.Any) -> bool:
        return (
            self.input_path == other.input_path
            and self.output_path == other.output_path
            and self.input_dir == other.input_dir
            and self.output_dir == other.output_dir
        )

    def __hash__(self) -> int:
        return hash(self.output_path)

    @property
    def url(self) -> str:
        dirname, basename = os.path.split(self.output_path)
        if basename == "index.html":
            if not dirname:
                return "/"
            return "/" + dirname.replace(os.path.sep, "/") + "/"
        return "/" + self.output_path.replace(os.path.sep, "/")

    @property
    def full_input_path(self) -> str:
        return os.path.join(self.input_dir, self.input_path)

    @property
    def full_output_path(self) -> str:
        return os.path.join(self.output_dir, self.output_path)

    def read_input_text(self) -> str:
        with open(self.full_input_path, "r") as input_file:
            return input_file.read()

    def write_output_text(self, text: str) -> None:
        with open(self.full_output_path, "w") as output_file:
            output_file.write(text)


class Files:
    """
    The collection of all the files that need to be built.
    """

    def __init__(self, files: typing.List[File] = None) -> None:
        self._files_list = []  # type: typing.List[File]
        self._files_by_input_path = {}  # type: typing.Dict[str, File]
        self._files_by_url_path = {}  # type: typing.Dict[str, File]
        if files is not None:
            for file in files:
                self.append(file)

    def __iter__(self) -> typing.Iterator[File]:
        return iter(self._files_list)

    def __len__(self) -> int:
        return len(self._files_list)

    def __eq__(self, other: typing.Any) -> bool:
        return self._files_list == other._files_list

    def __getitem__(self, index: int) -> File:
        return self._files_list[index]

    def __add__(self, other: "Files") -> "Files":
        return Files(self._files_list + other._files_list)

    def __iadd__(self, other: "Files") -> "Files":
        for file in other:
            self.append(file)
        return self

    def append(self, file: File) -> None:
        existing = self._files_by_input_path.get(file.input_path)
        if existing is not None:
            self._files_list.remove(existing)
        self._files_list.append(file)
        self._files_by_input_path[file.input_path] = file
        self._files_by_url_path[file.url] = file

    def get_by_input_path(self, path: str) -> File:
        return self._files_by_input_path[path]

    def get_by_url_path(self, path: str) -> File:
        return self._files_by_url_path[path]


class NavGroup:
    """
    An item in the site-wide navigation that references a menu group.
    """

    is_page = False
    is_group = True

    def __init__(
        self, title: str, children: typing.List[typing.Union["NavGroup", "NavPage"]]
    ) -> None:
        self.is_active = False
        self.title = title
        self.children = children
        self.parent = None  # type: typing.Optional[NavGroup]
        for child in children:
            child.parent = self

    def __eq__(self, other: typing.Any) -> bool:
        return (
            type(self) == type(other)
            and self.title == other.title
            and self.children == other.children
        )

    def walk_pages(self) -> typing.List["NavPage"]:
        pages = []
        for child in self.children:
            pages.extend(child.walk_pages())
        return pages


class NavPage:
    """
    An item in the site-wide navigation that references a page.
    """

    is_page = True
    is_group = False

    def __init__(self, title: str, file: File) -> None:
        self.is_active = False
        self.title = title
        self.file = file
        self.previous = None  # type: typing.Optional[NavPage]
        self.next = None  # type: typing.Optional[NavPage]
        self.parent = None  # type: typing.Optional[NavGroup]
        self._nav = None  # type: typing.Optional[Nav]

    def __eq__(self, other: typing.Any) -> bool:
        return (
            type(self) == type(other)
            and self.title == other.title
            and self.file == other.file
        )

    def walk_pages(self) -> typing.List["NavPage"]:
        return [self]

    @property
    def nav(self) -> "Nav":
        assert self._nav is not None
        return self._nav

    @property
    def url(self) -> str:
        if self.nav.base_url is None:
            if self.nav.active_page is None:
                return self.file.url
            else:
                if self.file == self.nav.active_page.file:
                    return "."
                path = posixpath.relpath(self.file.url, self.nav.active_page.file.url)
                if self.file.url.endswith("/") and not path.endswith("/"):
                    path += "/"
                return path
        else:
            return urljoin(self.nav.base_url, self.file.url)


class Nav:
    def __init__(
        self, items: typing.List[typing.Union[NavGroup, NavPage]], base_url: str = None
    ) -> None:
        self.items = items
        self.active_page = None  # type: typing.Optional[NavPage]
        self.base_url = base_url

        # Get an list of all the NavPages, in order.
        pages = self.walk_pages()
        for page in pages:
            page._nav = self

        # Create a lookup from `File`->`NavPage`
        self.map_file_to_page = {page.file: page for page in pages}

        # Set the `.previous` and `.next` attributes on each page.
        indexes = range(len(pages))
        first_index = 0
        final_index = len(pages) - 1
        previous_pages = [
            None if idx == first_index else pages[idx - 1] for idx in indexes
        ]
        next_pages = [None if idx == final_index else pages[idx + 1] for idx in indexes]
        previous_current_next = zip(previous_pages, pages, next_pages)

        for previous_page, current_page, next_page in previous_current_next:
            if previous_page is not None:
                current_page.previous = previous_page
            if next_page is not None:
                current_page.next = next_page

    def __iter__(self) -> typing.Iterable[typing.Union[NavGroup, NavPage]]:
        return iter(self.items)

    def __getitem__(self, idx: int) -> typing.Union[NavGroup, NavPage]:
        return self.items[idx]

    def __len__(self) -> int:
        return len(self.items)

    def __bool__(self) -> bool:
        return bool(self.items)

    def __eq__(self, other: typing.Any) -> bool:
        return type(self) == type(other) and self.items == other.items

    def walk_pages(self) -> typing.List["NavPage"]:
        pages = []
        for item in self.items:
            pages.extend(item.walk_pages())
        return pages

    def lookup_page(self, file: File) -> typing.Optional[NavPage]:
        return self.map_file_to_page.get(file)

    def activate(self, file: File) -> None:
        self.active_page = self.lookup_page(file)
        nav_item = typing.cast(typing.Union[None, NavPage, NavGroup], self.active_page)
        while nav_item is not None:
            nav_item.is_active = True
            nav_item = nav_item.parent

    def deactivate(self) -> None:
        nav_item = typing.cast(typing.Union[None, NavPage, NavGroup], self.active_page)
        while nav_item is not None:
            nav_item.is_active = False
            nav_item = nav_item.parent
        self.active_page = None


class Env:
    """
    The entire set of build information.
    """

    def __init__(
        self, files: Files, nav: Nav, base_url: str = None, config: typing.Dict = None
    ) -> None:
        self.files = files
        self.nav = nav
        self.base_url = base_url
        self.config = {} if config is None else config

    def get_url(self, hyperlink: str, from_file: File) -> str:
        """
        Given a `hyperlink` which may be either a link to a local file,
        or a regular URL, determine the URL that it should be referenced as.

        We need to know which `from_file` we're referencing the link from, so that:

        * We can resolve any relative paths, against that file.
        * We can output the final URL as a relative path, if no base URL is set.
        """
        scheme, netloc, path, params, query, fragment = urlparse(hyperlink)
        if scheme and netloc:
            # Leave any absolute URLs as they are.
            return hyperlink

        if not scheme and not netloc and not path:
            # Leave any params/query/frament only URLs as they are:
            return hyperlink

        if path.startswith("/"):
            # Determine possible file that an absolute path URL might point to.
            file_path = path.replace("/", os.path.sep)
        else:
            # Determine possible file that a relative path URL might point to.
            file_path = path.replace("/", os.path.sep)
            file_path = os.path.join(os.path.dirname(from_file.input_path), file_path)
            file_path = os.path.normpath(file_path)

        try:
            # If the path links to a local file, use that to determine the URL.
            file = self.files.get_by_input_path(file_path)
        except KeyError:
            # If the path links to a built URL, use that.
            file = self.files.get_by_url_path(path)

        if self.base_url is None:
            # No `base_url` to use. Create a relative URL.
            scheme, netloc, path = ("", "", posixpath.relpath(file.url, from_file.url))
            if file.url.endswith("/") and not path.endswith("/"):
                path += "/"
        else:
            # Create an absolute URL, using the `base_url`.
            scheme, netloc, path, _, _, _ = urlparse(urljoin(self.base_url, file.url))

        # Include any `params`, `query`, or `fragment` components that were present.
        return urlunparse((scheme, netloc, path, params, query, fragment))
