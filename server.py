#!/usr/bin/env python3
"""
Main server file. Runs a flask server which can be used to upload and download files.
"""
# pylint: disable=missing-function-docstring

from socket import AF_INET

from flask import Flask, redirect, render_template, request, jsonify
from flask_qrcode import QRcode
from werkzeug.serving import get_interface_ip
from werkzeug.utils import secure_filename

HOSTNAME = "0.0.0.0"
PORT = 8000
IP = f"http://{get_interface_ip(AF_INET)}:{PORT}"

app = Flask(__name__)
QRcode(app)


@app.route("/")
def root():
    return render_template("index.html", ip=IP)


# @app.errorhandler(404)
# def page_not_found(error):
    # _ = error
    # print("had 404")
    # return redirect("/")


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    if file:
        file.save(f"files/{secure_filename(file.filename)}")
    return redirect("/")


if __name__ == "__main__":
    app.run(host=HOSTNAME, port=PORT, debug=True)
