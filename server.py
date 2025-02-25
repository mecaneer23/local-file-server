#!/usr/bin/env python3
"""
Main server file. Runs a flask server which can be used to upload and download files.
"""

from argparse import ArgumentParser, Namespace
from pathlib import Path
from socket import AF_INET

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,  # pyright: ignore
)
from flask_qrcode import QRcode
from qrcode.main import QRCode
from werkzeug.serving import get_interface_ip
from werkzeug.utils import secure_filename
from werkzeug.wrappers import Response

HOSTNAME = "0.0.0.0"
PORT = 8000
IP = f"http://{get_interface_ip(AF_INET)}:{PORT}"
FOLDER = "files"

app = Flask(__name__)
app.secret_key = "Some"
QRcode(app)
local_path = Path(__file__).parent.joinpath(FOLDER)


def print_qrcode(data: str) -> None:
    """Print a qrcode to the terminal"""
    qr = QRCode()
    qr.add_data(data)
    qr.make(fit=True)
    qr.print_ascii(invert=True)


@app.route("/")
def root() -> str:
    """
    Entry point and home page. Render templates/index.html or
    return list of files for CLI requests
    """
    files = map(lambda path: path.name, local_path.iterdir())

    if request.accept_mimetypes.best == "text/html":
        return render_template(
            "index.html",
            ip=IP,
            files=files,
        )
    return "\n".join(files)


@app.route(f"/{FOLDER}/<path:filename>", methods=["GET", "POST"])
def download(filename: str) -> Response:
    """
    Navigating to the a file path
    for a valid file will download that file.
    """
    return send_from_directory(local_path, filename)


@app.route("/delete/<path:filename>", methods=["GET"])
def delete(filename: str) -> Response:
    """
    Navigating to /delete/filename will delete filename
    """
    try:
        local_path.joinpath(filename).unlink()
    except FileNotFoundError:
        flash("File not found, no file deleted")
    return redirect("/")


@app.route("/upload", methods=["POST"])
def upload() -> Response:
    """
    Accept a POST request with a file object.
    If it is valid, upload it to the server.
    """
    files = request.files.getlist("file")
    if not files:
        flash("No file provided")
        return redirect("/")
    for file in files:
        path = local_path.joinpath(secure_filename(str(file.filename)))
        if path.exists():
            flash("Filename already exists on server")
            return redirect("/")
        file.save(path)
    return redirect("/")


def get_args() -> Namespace:
    """Get command line arguments to local file server"""
    parser = ArgumentParser(
        description="Flask server to upload and download files on a local area network",
    )
    parser.add_argument(
        "download_folder",
        nargs="?",
        default=FOLDER,
        help=f"Folder to store and display downloads. Default is `{FOLDER}`",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for local file server"""
    global local_path  # pylint: disable=global-statement

    args = get_args()
    local_path = Path(args.download_folder)
    print_qrcode(IP)
    app.run(
        host=HOSTNAME,
        port=PORT,
        debug=True,
    )


if __name__ == "__main__":
    main()
