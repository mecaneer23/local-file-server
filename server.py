#!/usr/bin/env python3
"""
Main server file. Runs a flask server which can be used to upload and download files.
"""
# pylint: disable=missing-function-docstring

from socket import AF_INET

from flask import Flask, redirect, render_template
from werkzeug.serving import get_interface_ip
from flask_qrcode import QRcode


HOSTNAME = "0.0.0.0"
PORT = 8000
IP = f"http://{get_interface_ip(AF_INET)}:{PORT}"

app = Flask(__name__)
QRcode(app)


@app.route("/")
def root():
    return render_template("index.html", ip=IP)


@app.errorhandler(404)
def page_not_found(error):
    _ = error
    return redirect("/")


app.run(host=HOSTNAME, port=PORT, debug=True)
