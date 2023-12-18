#!/usr/bin/env python3
"""
Main server file. Runs a flask server which can be used to upload and download files.
"""
# pylint: disable=missing-function-docstring

import os
from socket import AF_INET

from flask import Flask, redirect, render_template, request, flash, send_from_directory
from flask_qrcode import QRcode
from werkzeug.serving import get_interface_ip
from werkzeug.utils import secure_filename

HOSTNAME = "0.0.0.0"
PORT = 80
IP = f"http://{get_interface_ip(AF_INET)}:{PORT}"

app = Flask(__name__)
app.secret_key = "Some"
QRcode(app)


@app.route("/")
def root():
    return render_template("index.html", ip=IP, files=os.listdir("files/"))


@app.route('/files/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    return send_from_directory("files", filename)


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    path = f"files/{secure_filename(file.filename)}"
    if not file:
        flash("No file provided")
        return redirect("/")
    if os.path.exists(os.path.join(path)):
        flash("Filename already exists on server")
        return redirect("/")
    file.save(path)
    flash(f"{file.filename} was uploaded successfully")
    return redirect("/")


if __name__ == "__main__":
    app.run(host=HOSTNAME, port=PORT, debug=True)
