#!/usr/bin/env python3
"""
Main server file. Runs a flask server which can be used to upload and download files.
"""
# pylint: disable=missing-function-docstring

from flask import Flask, render_template, redirect

app = Flask(__name__)

@app.route("/")
def root():
    return render_template("index.html")

@app.errorhandler(404)
def page_not_found(error):
    _ = error
    return redirect("/")

app.run(host="0.0.0.0", port=8000, debug=True)
