import os
from mkdocs2 import core, convertors, types


def write_file(path, text):
    """
    Helper function to write 'text' to the file at 'path'.
    """
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(path, "w") as output:
        output.write(text)


def test_gather_files(tmpdir):
    """
    Ensure that `gather_files` collects all the files in the input directory.
    """
    input_dir = os.path.join(tmpdir, "input")
    output_dir = os.path.join(tmpdir, "output")
    template_dir = os.path.join(tmpdir, "templates")

    config = {"site": {"url": "/"}, "build": {"template_dir": template_dir}}
    markdown_convertor = convertors.MarkdownConvertor(config=config)

    index_md = os.path.join(input_dir, "index.md")
    a_md = os.path.join(input_dir, "a.md")
    b_md = os.path.join(input_dir, "b", "b.md")
    write_file(index_md, "index")
    write_file(a_md, "aaa")
    write_file(b_md, "bbb")
    file_convertors = {"**.md": markdown_convertor}

    files = core.gather_files(
        input_dir=input_dir, output_dir=output_dir, file_convertors=file_convertors
    )
    assert files == types.Files(
        [
            types.File(
                input_rel_path="a.md",
                output_rel_path=os.path.join("a", "index.html"),
                input_dir=input_dir,
                output_dir=output_dir,
                convertor=markdown_convertor,
            ),
            types.File(
                input_rel_path=os.path.join("b", "b.md"),
                output_rel_path=os.path.join("b", "b", "index.html"),
                input_dir=input_dir,
                output_dir=output_dir,
                convertor=markdown_convertor,
            ),
            types.File(
                input_rel_path="index.md",
                output_rel_path="index.html",
                input_dir=input_dir,
                output_dir=output_dir,
                convertor=markdown_convertor,
            ),
        ]
    )


def test_overwrite_files(tmpdir):
    """
    Adding `gather_files` together should allow overwriting, so that
    only one instance is included for each unique input path.

    ie. docs files can override theme files.
    """
    primary_input_dir = os.path.join(tmpdir, "primary")
    secondary_input_dir = os.path.join(tmpdir, "secondary")
    output_dir = os.path.join(tmpdir, "output")
    template_dir = os.path.join(tmpdir, "templates")

    config = {"site": {"url": "/"}, "build": {"template_dir": template_dir}}
    markdown_convertor = convertors.MarkdownConvertor(config=config)
    static_file_convertor = convertors.StaticFileConvertor(config=config)

    primary_txt = os.path.join(primary_input_dir, "a.txt")
    secondary_txt = os.path.join(secondary_input_dir, "a.txt")
    write_file(primary_txt, "aaa")
    write_file(secondary_txt, "bbb")

    secondary = core.gather_files(input_dir=secondary_input_dir, output_dir=output_dir)
    primary = core.gather_files(input_dir=primary_input_dir, output_dir=output_dir)
    files = secondary + primary

    assert len(files) == 1
    assert files == types.Files(
        [
            types.File(
                input_rel_path="a.txt",
                output_rel_path="a.txt",
                input_dir=primary_input_dir,
                output_dir=output_dir,
                convertor=static_file_convertor,
            )
        ]
    )


def test_load_nav():
    input_dir = "input"
    output_dir = "output"
    template_dir = "templates"

    config = {"site": {"url": "/"}, "build": {"template_dir": template_dir}}
    markdown_convertor = convertors.MarkdownConvertor(config=config)

    files = types.Files(
        [
            types.File(
                input_rel_path="index.md",
                output_rel_path="index.html",
                input_dir=input_dir,
                output_dir=output_dir,
                convertor=markdown_convertor,
            ),
            types.File(
                input_rel_path=os.path.join("topics", "a.md"),
                output_rel_path=os.path.join("topics", "a", "index.html"),
                input_dir=input_dir,
                output_dir=output_dir,
                convertor=markdown_convertor,
            ),
            types.File(
                input_rel_path=os.path.join("topics", "b.md"),
                output_rel_path=os.path.join("topics", "b", "index.html"),
                input_dir=input_dir,
                output_dir=output_dir,
                convertor=markdown_convertor,
            ),
        ]
    )

    nav_info = {
        "Home": "index.md",
        "Topics": {
            "Topic A": os.path.join("topics", "a.md"),
            "Topic B": os.path.join("topics", "b.md"),
        },
    }

    nav = core.load_nav_info(nav_info, files)
    assert nav == [
        types.NavPage(title="Home", file=files[0]),
        types.NavGroup(
            title="Topics",
            children=[
                types.NavPage(title="Topic A", file=files[1]),
                types.NavPage(title="Topic B", file=files[2]),
            ],
        ),
    ]

    home = nav[0]
    topics = nav[1]
    topic_a = topics.children[0]
    topic_b = topics.children[1]
    assert home.parent is None
    assert topics.parent is None
    assert topic_a.parent is topics
    assert topic_b.parent is topics


def test_urls_for_files():
    config = {"site": {"url": "/"}, "build": {"template_dir": "templates"}}
    markdown_convertor = convertors.MarkdownConvertor(config=config)

    file = types.File(
        input_rel_path="index.md",
        output_rel_path="index.html",
        input_dir="input",
        output_dir="output",
        convertor=markdown_convertor,
    )
    assert file.url == "/"

    file = types.File(
        input_rel_path="page.html",
        output_rel_path="page.html",
        input_dir="input",
        output_dir="output",
        convertor=markdown_convertor,
    )
    assert file.url == "/page.html"


def test_url_function():
    config = {"site": {"url": "/"}, "build": {"template_dir": "templates"}}
    markdown_convertor = convertors.MarkdownConvertor(config=config)
    input_dir = "input"
    output_dir = "output"

    files = types.Files(
        [
            types.File(
                input_rel_path="index.md",
                output_rel_path="index.html",
                input_dir=input_dir,
                output_dir=output_dir,
                convertor=markdown_convertor,
            ),
            types.File(
                input_rel_path=os.path.join("topics", "a.md"),
                output_rel_path=os.path.join("topics", "a", "index.html"),
                input_dir=input_dir,
                output_dir=output_dir,
                convertor=markdown_convertor,
            ),
            types.File(
                input_rel_path=os.path.join("topics", "b.md"),
                output_rel_path=os.path.join("topics", "b", "index.html"),
                input_dir=input_dir,
                output_dir=output_dir,
                convertor=markdown_convertor,
            ),
        ]
    )

    assert files[0].url == "/"
    assert files[1].url == "/topics/a/"
    assert files[2].url == "/topics/b/"

    # No base URL.
    url = core.url_function_for_file(files[0], files)
    assert url("#anchor") == "#anchor"
    assert url("https://www.example.com") == "https://www.example.com"
    assert url("topics/a.md") == "topics/a/"
    assert url("topics/b.md") == "topics/b/"
    assert url("/topics/a/") == "topics/a/"
    assert url("/topics/b/") == "topics/b/"

    url = core.url_function_for_file(files[1], files)
    assert url("../index.md") == "../../"
    assert url("b.md") == "../b/"
    assert url("/") == "../../"
    assert url("/topics/b/") == "../b/"

    url = core.url_function_for_file(files[2], files)
    assert url("../index.md") == "../../"
    assert url("a.md#anchor") == "../a/#anchor"
    assert url("/") == "../../"
    assert url("/topics/a/#anchor") == "../a/#anchor"

    # Host relative base URL.
    url = core.url_function_for_file(files[0], files, base_url="/")
    assert url("#anchor") == "#anchor"
    assert url("https://www.example.com") == "https://www.example.com"
    assert url("topics/a.md") == "/topics/a/"
    assert url("topics/b.md") == "/topics/b/"
    assert url("/topics/a/") == "/topics/a/"
    assert url("/topics/b/") == "/topics/b/"

    url = core.url_function_for_file(files[1], files, base_url="/")
    assert url("../index.md") == "/"
    assert url("b.md") == "/topics/b/"
    assert url("/") == "/"
    assert url("/topics/b/") == "/topics/b/"

    url = core.url_function_for_file(files[2], files, base_url="/")
    assert url("../index.md") == "/"
    assert url("a.md#anchor") == "/topics/a/#anchor"
    assert url("/") == "/"
    assert url("/topics/a/#anchor") == "/topics/a/#anchor"

    # Absolute base URL.
    url = core.url_function_for_file(files[0], files, base_url="https://example.com")
    assert url("#anchor") == "#anchor"
    assert url("https://www.example.com") == "https://www.example.com"
    assert url("topics/a.md") == "https://example.com/topics/a/"
    assert url("topics/b.md") == "https://example.com/topics/b/"
    assert url("/topics/a/") == "https://example.com/topics/a/"
    assert url("/topics/b/") == "https://example.com/topics/b/"

    url = core.url_function_for_file(files[1], files, base_url="https://example.com")
    assert url("../index.md") == "https://example.com/"
    assert url("b.md") == "https://example.com/topics/b/"
    assert url("/") == "https://example.com/"
    assert url("/topics/b/") == "https://example.com/topics/b/"

    url = core.url_function_for_file(files[2], files, base_url="https://example.com")
    assert url("../index.md") == "https://example.com/"
    assert url("a.md#anchor") == "https://example.com/topics/a/#anchor"
    assert url("/") == "https://example.com/"
    assert url("/topics/a/#anchor") == "https://example.com/topics/a/#anchor"
