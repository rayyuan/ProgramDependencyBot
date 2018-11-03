from flask import Flask, request, render_template, abort, send_file
from requests_toolbelt import MultipartEncoder
import json, io, os
import parse_file, webex
import parse_file
from urllib.request import Request, urlopen
# from flask_pymongo import PyMongo

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("form.html")

@app.route("/webex", methods=["POST"])
def webex_request():
    webhook = json.loads(request.data)
    if webhook['data']['personEmail'] != os.environ["BOT_EMAIL"]:
        request_json = webex.sendGetRequest(os.environ["SPARK_MESSAGES_URL"] + webhook['data']['id'])
        query_url = json.loads(request_json).get("text")
        errmsg = {
            "roomId": webhook['data']['roomId'],
            "text": ""
        }
        if query_url is None:
            errmsg["text"] = "{0} takes in a Python GitHub URL".format(os.environ["BOT_NAME"])
            webex.sendErrorMsg(os.environ["SPARK_MESSAGES_URL"], errmsg)
            abort(400, "No URL sent")
        try:
            im = parse_file.gh_link_entry(query_url)
        except AssertionError as e:
            errmsg["text"] = "Invalid input. Must be a valid Python GitHub URL and option (e.g. `-g=5`)."
            webex.sendErrorMsg(os.environ["SPARK_MESSAGES_URL"], errmsg)
            abort(400, "Invalid URL")

        output = io.BytesIO()
        im.save(output, format="PNG")
        out_message = "Visualization of {0}".format(query_url[len(os.environ["BOT_NAME"]):])

        fields = {
            "roomId": webhook['data']['roomId'],
            "text": out_message,
            "files": ("visualize.png", output, "image/png")
        }
        data = MultipartEncoder(fields=fields)
        webex.sendPostRequest(os.environ["SPARK_MESSAGES_URL"], data)
    return "true"

@app.route("/", methods=['POST'])
def form_submission():
    url = request.form['text']
    try:
        im = parse_file.gh_link_entry(url)
    except AssertionError as e:
        # ("Invalid input. Must be a valid Python Github URL and option (e.g. '-g=5).")
        return render_template("form.html", error=e)
    output = io.BytesIO()
    im.save(output, format="PNG")
    return send_file(output, attachment_filename="someimage.png", mimetype="image/png")

if __name__ == "__main__":
    app.run(debug=True)
