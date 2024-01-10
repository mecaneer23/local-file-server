#!/usr/bin/env python3
"""
Main server file. Runs a flask server which can be used to upload and download files.
"""
# pylint: disable=missing-function-docstring

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
from werkzeug.wrappers import Response
from werkzeug.serving import get_interface_ip
from werkzeug.utils import secure_filename

HOSTNAME = "0.0.0.0"
PORT = 8000
IP = f"http://{get_interface_ip(AF_INET)}:{PORT}"
FOLDER = "files"

app = Flask(__name__)
app.secret_key = "Some"
QRcode(app)
local_path = Path(__file__).parent


@app.route("/")
def root():
    return render_template(
        "index.html",
        ip=IP,
        files=map(lambda path: path.name, local_path.joinpath(FOLDER).iterdir()),
    )


@app.route(f"/{FOLDER}/<path:filename>", methods=["GET", "POST"])
def download(filename: str) -> Response:
    return send_from_directory(local_path.joinpath(FOLDER), filename)


@app.route("/upload", methods=["POST"])
def upload() -> Response:
    file = request.files["file"]
    if not file:
        flash("No file provided")
        return redirect("/")
    path = local_path.joinpath(FOLDER, secure_filename(str(file.filename)))
    if path.exists():
        flash("Filename already exists on server")
        return redirect("/")
    file.save(path)  # pyright: ignore
    flash(f"{file.filename} was uploaded successfully")
    return redirect("/")


if __name__ == "__main__":
    app.run(host=HOSTNAME, port=PORT, debug=False)
