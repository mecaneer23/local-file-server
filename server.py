#!/usr/bin/env python3
"""
Main server file. Runs a flask server which can be used to
upload and download files.
"""

from argparse import ArgumentParser, Namespace
from enum import Enum
from pathlib import Path
from re import search
from socket import AF_INET

from flask import (
    Flask,
    Request,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
)
from flask_qrcode import QRcode
from qrcode.main import QRCode
from werkzeug.serving import get_interface_ip
from werkzeug.utils import secure_filename
from werkzeug.wrappers import Response

HOSTNAME = "0.0.0.0"  # socket.gethostbyname_ex(socket.gethostname())
PORT = 8000
IP = f"http://{get_interface_ip(AF_INET)}:{PORT}"
FOLDER = "files"

app = Flask(__name__)
app.secret_key = "secret"  # noqa: S105 # debug mode flashing breaks without a secret key
QRcode(app)
local_path = Path(__file__).parent.joinpath(FOLDER)


class RequestOrigin(Enum):
    """Enumeration of possible request origins"""

    CLI = "CLI"
    WEB = "WEB"


def print_qrcode(data: str) -> None:
    """Print a qrcode to the terminal"""
    qr = QRCode()
    qr.add_data(data)
    qr.make(fit=True)
    qr.print_ascii(invert=True)


def get_likely_request_origin(request_: Request) -> RequestOrigin:
    """Return the most likely request origin"""
    return (
        RequestOrigin.WEB
        if str(request_.accept_mimetypes.best).split(";", maxsplit=1)[0]
        in [
            "application/signed-exchange",
            "text/html",
        ]
        else RequestOrigin.CLI
    )


@app.route("/")
def root() -> Response:
    """
    Entry point and home page. Render templates/index.html or
    return list of files for CLI requests
    """
    files = (path.name for path in local_path.iterdir())

    if get_likely_request_origin(request) == RequestOrigin.WEB:
        return make_response(
            render_template(
                "index.html",
                ip=IP,
                files=files,
            ),
        )
    return Response(
        "\n".join(files) + "\n",
        status=200,
        mimetype="text/plain",
    )


@app.route(f"/{FOLDER}/<path:filename>", methods=["GET"])
def download(filename: str) -> Response:
    """
    Navigating to the a file path
    for a valid file will download that file.
    """
    return send_from_directory(local_path, secure_filename(filename))


@app.route("/delete/<path:filename>", methods=["GET", "DELETE"])
def delete(filename: str) -> Response:
    """
    Navigating to /delete/filename will delete filename
    """
    try:
        local_path.joinpath(filename).unlink()
    except FileNotFoundError:
        error_message = f'File "{filename}" not found, no file deleted'
        flash(error_message)
        return (
            redirect("/")
            if get_likely_request_origin(request) == RequestOrigin.WEB
            else Response(
                f"{error_message}\n",
                status=405,
                mimetype="text/plain",
            )
        )
    return (
        redirect("/")
        if get_likely_request_origin(request) == RequestOrigin.WEB
        else Response(
            f"{filename}\n",
            status=204,
            mimetype="text/plain",
        )
    )


@app.route("/upload", methods=["PUT"])
@app.route("/upload/", methods=["PUT"])
@app.route("/upload/<path:filename>", methods=["PUT"])
def upload_put(filename: str | None = None) -> Response:
    """
    Accept a PUT request with a file object.
    If it is valid, upload it to the server.
    Handle raw binary upload (curl --upload-file/-T)
    """
    if not filename:
        # There isn't a way to detect the value of -T in Flask. Potentially
        # implement file uploading without specified filename (uploaded_file(n))
        return Response(
            "405: make sure the path ends with `/`"
            "and a file is provided\nNo file uploaded\n",
            status=405,
            mimetype="text/plain",
        )
    path = local_path.joinpath(secure_filename(filename))
    if path.exists():
        return Response(
            f'Filename "{filename}" already exists on server\n',
            status=409,
            mimetype="text/plain",
        )
    with Path(path).open("wb") as file:
        file.write(request.data)
    return Response(filename + "\n", status=201, mimetype="text/plain")


def upload_duplicate_fail(filename: str | None) -> Response:
    """Handle `fail` option when duplicate file upload is attempted"""
    error_message = f"Filename `{filename}` already exists on server"
    if get_likely_request_origin(request) == RequestOrigin.WEB:
        flash(error_message)
        return redirect("/")
    return Response(
        error_message + "\n",
        status=409,
        mimetype="text/plain",
    )


def increment_number(path: Path) -> Path:
    """Append a `_number` to the end of a Path"""
    suffix = path.suffix
    stem = path.stem

    stem = (
        f"{stem[:-1]}{int(stem[-1]) + 1}"
        if search(r"_\d$", stem)
        else f"{stem}_1"
    )
    return path.parent / Path(stem + suffix)


@app.route("/upload", methods=["POST"])
@app.route("/upload/", methods=["POST"])
def upload_post() -> Response:
    """
    Accept a POST request with a file object.
    If it is valid, upload it to the server.
    Handle multipart/form-data upload (curl --form/-F or web)
    """
    files = request.files.getlist("file")
    if not files:
        error_message = "No file provided"
        if get_likely_request_origin(request) == RequestOrigin.WEB:
            flash(error_message)
            return redirect("/")
        return Response(
            error_message + "\n",
            status=405,
            mimetype="text/plain",
        )
    behavior = request.form["duplicate-file-behavior"]
    for file in files:
        path = local_path.joinpath(secure_filename(str(file.filename)))
        if behavior == "keep":
            while path.exists():
                path = increment_number(path)
            file.save(path)
            continue
        if path.exists():
            if behavior == "fail":
                return upload_duplicate_fail(file.filename)
            if behavior == "skip":
                continue
        file.save(path)
    return (
        redirect("/")
        if get_likely_request_origin(request) == RequestOrigin.WEB
        else Response(
            "\n".join(str(file.filename) for file in files) + "\n",
            status=201,
            mimetype="text/plain",
        )
    )


def format_markdown_section(filepath: Path, first_line: str) -> str:
    """
    Return a formatted and easy-to-read string
    from a section of a markdown file
    """
    with filepath.open(encoding="utf-8") as file:
        data = file.readlines()
    useful_data: list[str] = []
    for line in data[data.index(first_line) :]:
        usable_line = line
        if line.startswith("```"):
            continue
        if line.startswith("###"):
            usable_line = line.lstrip("# ").rstrip("\n") + ":"
        useful_data.append(usable_line)
    return "".join(useful_data).replace("\n\n\n", "\n")


@app.route("/api")
def api() -> Response:
    """API endpoint for retrieving help information"""
    if get_likely_request_origin(request) == RequestOrigin.WEB:
        return Response(
            "CLI Help: try calling this url with a CLI tool",
            status=406,
            mimetype="text/plain",
        )
    return Response(
        format_markdown_section(
            Path("README.md"),
            "### CLI - simplified examples\n",
        ),
        status=200,
        mimetype="text/plain",
    )


def get_args() -> Namespace:
    """Get command line arguments to local file server"""
    parser = ArgumentParser(
        description="Flask server to upload and download "
        "files on a local area network",
    )
    parser.add_argument(
        "download_folder",
        nargs="?",
        default=FOLDER,
        help=f"Folder to store and display downloads. Default is `{FOLDER}`",
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        default=False,
        help="Boolean: enter debug mode",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for local file server"""
    global local_path  # pylint: disable=global-statement  # noqa: PLW0603

    args = get_args()
    local_path = Path(args.download_folder)
    print_qrcode(IP)
    print(IP)  # noqa: T201
    app.run(
        host=HOSTNAME,
        port=PORT,
        debug=args.debug,
    )


if __name__ == "__main__":
    main()
