from click.testing import CliRunner
from mkdocs2.cli import cli
import os


def write_file(path, text):
    """
    Helper function to write 'text' to the file at 'path'.
    """
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(path, "w") as output:
        output.write(text)


def test_build(tmpdir):
    input_dir = os.path.join(tmpdir, "input")
    output_dir = os.path.join(tmpdir, "output")
    template_dir = os.path.join(tmpdir, "templates")

    config = os.path.join(tmpdir, "mkdocs.yml")
    base_html = os.path.join(template_dir, "base.html")
    index_md = os.path.join(input_dir, "index.md")
    image_png = os.path.join(input_dir, "image.png")
    favicon = os.path.join(input_dir, "favicon.ico")
    a_md = os.path.join(input_dir, "topics", "a.md")
    b_md = os.path.join(input_dir, "topics", "b.md")
    write_file(
        index_md,
        "# index\n![image](image.png)\n* [link to a](topics/a.md)\n* [link to b](topics/b.md)",
    )
    write_file(a_md, "# a\n* [link to b](b.md)\n *[link to index](../index.md)")
    write_file(b_md, "# b\n* [link to a](a.md)\n *[link to index](../index.md)")
    write_file(favicon, "xxx")
    write_file(image_png, "xxx")
    write_file(base_html, "<html><body>{{ content }}</body></html>")

    write_file(
        config,
        """
build:
    url: /
    input_dir: input
    output_dir: output
    template_dir: templates
nav:
    Homepage: index.md
    Topics:
        Topic A: topics/a.md
        Topic B: topics/b.md
convertors:
    - mkdocs2.convertors.MarkdownPages
    - mkdocs2.convertors.StaticFiles
""",
    )

    os.chdir(tmpdir)
    runner = CliRunner()
    result = runner.invoke(cli, ["build"])
    assert result.exit_code == 0
