import click
import http.server
import mkdocs2
import os
import socketserver
import tempfile
import typing
import yaml


@click.command()
@click.option("--config", "config_file", type=click.File(), default="mkdocs.yml")
def build(config_file: typing.TextIO) -> None:
    content = config_file.read()
    config = yaml.load(content)
    mkdocs2.build(config)


@click.command()
@click.option("--config", "config_file", type=click.File(), default="mkdocs.yml")
def serve(config_file: typing.TextIO) -> None:  # pragma: nocover
    content = config_file.read()
    config = yaml.load(content)

    with tempfile.TemporaryDirectory() as tmpdir:
        config["site"]["url"] = "/"
        config["build"]["output_dir"] = tmpdir
        mkdocs2.build(config)
        os.chdir(tmpdir)
        addr = ("", 8000)
        handler = http.server.SimpleHTTPRequestHandler
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(addr, handler) as httpd:
            msg = 'Documentation available at "http://127.0.0.1:8000/" (Ctrl+C to quit)'
            click.echo(msg)
            httpd.serve_forever()


@click.group()
def cli() -> None:
    pass


cli.add_command(build)
cli.add_command(serve)
