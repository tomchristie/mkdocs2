import os
import typing


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

    def activate(self, file: File) -> None:
        for child in self.children:
            child.activate(file)

    def deactivate(self) -> None:
        self.is_active = False
        for child in self.children:
            child.deactivate()


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
        self.parent = None  # type: typing.Optional[NavGroup]

    def __eq__(self, other: typing.Any) -> bool:
        return (
            type(self) == type(other)
            and self.title == other.title
            and self.file == other.file
        )

    def activate(self, file: File) -> None:
        if file == self.file:
            nav = self
            while nav is not None:
                nav.is_active = True
                nav = nav.parent

    def deactivate(self) -> None:
        self.is_active = False


class Nav:
    def __init__(self, items: typing.List[typing.Union[NavGroup, NavPage]]):
        self.items = items

    def __iter__(self) -> typing.Iterable[typing.Union[NavGroup, NavPage]]:
        return iter(self.items)

    def __getitem__(self, idx: int) -> typing.Union[NavGroup, NavPage]:
        return self.items[idx]

    def __eq__(self, other: typing.Any) -> bool:
        return type(self) == type(other) and self.items == other.items

    def activate(self, file: File) -> None:
        for item in self.items:
            item.activate(file)

    def deactivate(self) -> None:
        for item in self.items:
            item.deactivate()


class Env:
    """
    The entire set of build information.
    """

    def __init__(self, files: Files, nav: Nav, config: typing.Dict) -> None:
        self.files = files
        self.nav = nav
        self.config = config
