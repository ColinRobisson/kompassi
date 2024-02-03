import collections.abc
import contextlib
import os
import shutil
import tempfile
import typing
import zipfile

import django.utils.lorem_ipsum
import jinja2.nodes
import weasyprint
from django.http import FileResponse, HttpResponse, HttpResponseBase
from jinja2 import FunctionLoader
from jinja2.sandbox import SandboxedEnvironment

from . import filters
from .files import Lut, NameFactory, make_lut, make_name
from .models import FileVersion, ProjectFile

DEBUG = False

FileWithData = tuple[str, dict[str, str] | None]
DataRow = dict[str, str | dict[str, typing.Any]]
DataSet = list[DataRow]
Vfs = dict[str, FileVersion]

LOCAL_FILE_URI_PREFIX = "file:///"


def html_header(title: str, lang: str = "fi") -> str:
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
     <meta charset="utf-8">
     <title>{title}</title>
</head>\n"""


def html_footer() -> str:
    return "\n</html>\n"


def ls_r(path: str) -> None:
    for ent in os.scandir(path):
        print(ent.path)
        if ent.is_dir():
            ls_r(ent.path)


def files_to_vfs(files: typing.Iterable[FileVersion]) -> Vfs:
    return {file_version.file.file_name: file_version for file_version in files}


def find_main(files: typing.Iterable[FileVersion]) -> FileVersion | None:
    for file_version in files:
        if file_version.file.type == ProjectFile.Type.Main:
            return file_version
    return None


def find_lookup_tables(files: typing.Iterable[FileVersion]) -> dict[str, Lut]:
    return {
        make_name(file_version.file.file_name): make_lut(file_version.data, "utf-8")
        for file_version in files
        if file_version.file.type == ProjectFile.Type.CSV
    }


@contextlib.contextmanager
def make_temp_dir(*, keep: bool) -> collections.abc.Generator[str, None, None]:
    tmp_dir = tempfile.mkdtemp()
    try:
        yield tmp_dir
    finally:
        if not keep:
            shutil.rmtree(tmp_dir)


def render_pdf(
    files: typing.Iterable[FileVersion],
    filename_pattern: str | None,
    title_pattern: str,
    data: DataSet,
    *,
    return_archive: bool = False,
) -> HttpResponseBase:
    main = find_main(files)
    if main is None:
        return HttpResponse("Main file not found", status=404)

    vfs = files_to_vfs(files)
    env = _TemplateCompiler(vfs)
    if DEBUG:
        print(vfs)

    if DEBUG:
        print(data)

    with make_temp_dir(keep=False) as tmpdir:
        # tmpdir contents in the end (S for single file output, A for archive/split output):
        # - src/
        #   - master.html (S)
        #   - 001.html (A)
        #   - 002.html ...
        # - result/
        #   - master.pdf (S)
        #   - 001.pdf (A)
        #   - 002.pdf ...
        # - result.zip (A)

        # Either result/master.pdf or result.zip is streamed out.
        # master.pdf (S) is renamed when streamed.
        # ???.pdf (A) are renamed when written into the zip.

        src_dir = os.path.join(tmpdir, "src")
        result_dir = os.path.join(tmpdir, "result")
        os.mkdir(src_dir)
        os.mkdir(result_dir)

        # Compile source templates into one or more html's into $tmpdir/src.
        sources: list[FileWithData] = env.compile(
            main.file.file_name, src_dir, data, title_pattern, split_output=return_archive
        )

        wp = _HtmlCompiler(vfs)
        results: list[FileWithData] = wp.compile(sources, result_dir)
        name_tpl = env.from_string(filename_pattern) if filename_pattern else None
        name_factory = NameFactory(name_tpl)

        if return_archive:
            z_name = os.path.join(tmpdir, "result.zip")
            with zipfile.ZipFile(z_name, "w") as z:
                for pdf_name, row in results:
                    arc_name = name_factory.make({"row": row}, fallback=os.path.basename(pdf_name))
                    z.write(pdf_name, arcname=arc_name)
            if DEBUG:
                ls_r(tmpdir)
            # FileResponse closes the open file by itself.
            return FileResponse(open(z_name, "rb"), content_type="application/zip")  # noqa: SIM115

        if len(results) > 1:
            return HttpResponse(status=401)

        if results:
            pdf_name, row = results[0]
            file_name = name_factory.make({"row": row}, fallback="result.pdf")
            # FileResponse closes the open file by itself.
            return FileResponse(
                open(pdf_name, "rb"),  # noqa: SIM115
                content_type="application/pdf",
                filename=file_name,
            )

        return HttpResponse(status=201)


class _TemplateCompiler:
    def __init__(self, vfs: Vfs) -> None:
        self.vfs = vfs

        env = SandboxedEnvironment(
            autoescape=True,
            loader=FunctionLoader(self._do_lookup),
        )

        filters.add_all_to(env.filters)
        env.globals["lorem"] = django.utils.lorem_ipsum.paragraphs

        self.env = env

    def from_string(self, s: str | None) -> jinja2.Template | None:
        if s is None:
            return None
        return self.env.from_string(s)

    def get_source(self, file_name: str) -> str:
        return self.env.loader.get_source(self.env, file_name)[0]

    def parse(self, source: str) -> jinja2.nodes.Template:
        return self.env.parse(source)

    def compile(
        self, main_file_name: str, src_dir: str, data: DataSet, title_pattern: str, *, split_output: bool
    ) -> list[FileWithData]:
        lookups = find_lookup_tables(self.vfs.values())
        tpl = self.env.get_template(main_file_name)
        title_pattern = self.from_string(title_pattern)

        sources: list[FileWithData] = []
        if split_output:
            for idx, row in enumerate(data, start=1):
                row_copy = dict(row)
                title = title_pattern.render(row=row_copy)

                src_name = os.path.join(src_dir, f"{idx:03d}.html")
                sources.append((src_name, row_copy))

                with open(src_name, "w") as of:
                    of.write(html_header(title=title))
                    of.write(tpl.render(row=row_copy, **lookups))
                    of.write(html_footer())
        else:
            # Render title if we have any data, but supply the row only if it is singular.
            row_copy = dict(data[0]) if len(data) == 1 else None
            title = title_pattern.render(row=row_copy) if data else ""

            src_name = os.path.join(src_dir, "master.html")
            sources.append((src_name, row_copy))

            with open(src_name, "w") as of:
                of.write(html_header(title=title))
                for row in data:
                    of.write(tpl.render(row=dict(row), **lookups))
                of.write(html_footer())
        return sources

    # See `jinja2.loaders.FunctionLoader.__init__` for function signature.
    def _do_lookup(
        self,
        name: str,
    ) -> tuple[str, str, typing.Callable[[], bool]] | None:
        the_file: FileVersion | None = self.vfs.get(name)
        if DEBUG:
            print("Template lookup", name, the_file)
        if the_file is None:
            return None
        if the_file.file.type not in (
            ProjectFile.Type.Main,
            ProjectFile.Type.HTML,
            ProjectFile.Type.CSS,
        ):
            return None
        with the_file.data.open("rt") as tpl_file:
            src = tpl_file.read()
        return src, name, lambda: True


class _HtmlCompiler:
    def __init__(self, vfs: Vfs) -> None:
        self.vfs = vfs
        self.stylesheets = self.find_stylesheets(vfs.values())

    @staticmethod
    def find_stylesheets(files: typing.Iterable[FileVersion]) -> list[FileVersion]:
        return [file_version for file_version in files if file_version.file.type == ProjectFile.Type.CSS]

    def compile(self, sources: list[FileWithData], result_dir: str) -> list[FileWithData]:
        parsed_sheets = [
            weasyprint.CSS(
                string=sheet_file.data.read(),
                base_url=LOCAL_FILE_URI_PREFIX,
                url_fetcher=self._do_lookup,
            )
            for sheet_file in self.stylesheets
        ]
        results: list[FileWithData] = []
        for source, row in sources:
            pdf_html = weasyprint.HTML(
                filename=source,
                base_url=LOCAL_FILE_URI_PREFIX,
                url_fetcher=self._do_lookup,
            )
            pdf = pdf_html.write_pdf(
                stylesheets=parsed_sheets,
            )
            dst_base = os.path.splitext(os.path.basename(source))[0]
            dst_name = os.path.join(result_dir, dst_base + ".pdf")
            results.append((dst_name, row))
            with open(dst_name, "wb") as of:
                of.write(pdf)

        return results

    # See `weasyprint.urls.default_url_fetcher` for function signature.
    # Note: At least some exceptions are silently ignored by weasyprint.
    def _do_lookup(self, url: str, timeout: int = 10, ssl_context=None) -> dict:
        file_url = url.removeprefix(LOCAL_FILE_URI_PREFIX)
        if file_url == url:
            restricted_url = "Invalid URL to look up for"
            raise ValueError(restricted_url)
        the_file: FileVersion | None = self.vfs.get(file_url)
        if DEBUG:
            print("Pdf lookup", url, the_file)
        if the_file is None:
            raise KeyError
        return {
            "file_obj": the_file.data.open("rb"),
            # Weasyprint requires this to avoid file not found exc with the original filename.
            "redirected_url": file_url,
        }
