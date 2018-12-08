#
# Main of AppEngine service
#

from flask import Flask, request, redirect, make_response

import requests
import private

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)

@app.route("/")
def hello():
    return 'Hello World! This page is created by App Engine service2.'


@app.route('/checkAliveOfWebOnGCE')
def checkAliveOfWebOnGCE():
  try:
    url = "http://35.203.132.149:80/"+private.project_app
    r = requests.get(url)
    if r.status_code > 299:
        import myGmail
        myGmail.sendAlertMail("Alert Mail: server on GCE down", \
                              "Web server on GCE not respond. I am on AppEngine.")
        return "Checking alive of GCE Web server... NG."
    return "Checking alive of GCE Web server... OK."
  except:
    import myGmail
    myGmail.sendAlertMail("Alert Mail: error", "Error in checkAliveOfWebOnGCE() on AppEngine.")
    raise

# receive Kakeibo HTML 
@app.route("/"+private.project_app+"/kakeiboHtml", methods=['POST'])
def kakeiboHtml():
    data = request.form['body']
    return make_response(data,[("Content-Type","text/plain")])
    
# transfer to other server
@app.route('/<path:path>')
def catch_all_private(path):
    url = "http://35.203.132.149:80" + request.script_root + request.full_path
    print("redirecting to "+url)
    r = requests.get(url)
    return make_response(r.content, r.status_code)

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
