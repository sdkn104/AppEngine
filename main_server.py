#
# Web server (not on AppEngine)
#

from flask import Flask, request
import subprocess
import re

import myGmail
import myBigQuery
import myStock
import checkAlive
import sendJamInfoToBigQuery
import private

staticFolder = "/home/sdkn104home/static"

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__, static_folder=staticFolder)


@app.route("/")
@app.route("/"+private.project_app)
@app.route("/"+private.project_app+"/")
def hello():
    return 'Hello World! This page is created by Flask on Compute Engine.'

@app.route("/sendJamInfo")
@app.route("/"+private.project_app+"/sendJamInfo")
def sendJamInfo():
    sendJamInfoToBigQuery.send()
    return 'done'

@app.route("/checkAlive")
@app.route("/"+private.project_app+"/checkAlive")
def doCheckAlive():
    s = checkAlive.checkAlive()
    return s

@app.route("/"+private.project_app+"/insertBQ")
def insertBQ():
    table = request.args.get('table', '')
    value1 = request.args.get('value1', '')
    value2 = request.args.get('value2', '')
    value3 = request.args.get('value3', '')
    value4 = request.args.get('value4', '')
    myBigQuery.loadBigQuery(table, [[value1, value2, value3, value4]])
    import gc
    gc.collect()
    return 'done inserting to '+table+", ("+value1+", "+value2+", "+value3+", "+value4+")"

@app.route("/"+private.project_app+"/gmail")
def gmail():
    addr_to = request.args.get('to', '')
    subject = request.args.get('subject', '')
    body = request.args.get('body', '')
    if addr_to == "":
        addr_to = "sdkn104@yahoo.co.jp"
    myGmail.sendGmail("sdkn104home@gmail.com", addr_to, subject, body)
    return 'done sending gmail '+subject+" to "+addr_to

@app.route("/sendStock")
@app.route("/"+private.project_app+"/sendStock")
def sendStock():
    names_jp = ["1308", "1330", "9984", "1699", "6753", "7203","1639","1622"]
    names_bloom = ["NKY:IND", "INDU:IND", "USDJPY:CUR", "HKDJPY:CUR", "EURJPY:CUR", 
                   "VWO:US", "IYR:US", "IVV:US", "VNM:US",
                   "2836:HK"]
    names_bloom.extend([n+":JP" for n in names_jp])
    myStock.sendToBQ(names_jp, names_bloom, "stock_rcv")
    return 'done'

# ---- DOWNLOADER ----------

@app.route("/dl_top")
@app.route("/"+private.project_app+"/dl_top")
def download_top():
    return "<form action='/dl_download'>URL:<input type='text' name=url><br>File Name:<input type='text' name=fn><br><input type=submit value='download'></form><br><a href='/dl_ls'>dl_ls</a>"

@app.route("/dl_ls")
@app.route("/"+private.project_app+"/dl_ls")
def download_ls():
    proc = subprocess.run(["ls", "-l", staticFolder+"/uploads"], stdout=subprocess.PIPE, universal_newlines=True)
    dirs = proc.stdout.split("\n")
    dirs = [ re.sub(r'(.* +)([^ ]+) *$', r'\1 <a href="http://35.203.132.149/static/uploads/\2">\2</a><br>', line) for line in dirs]
    return "\n".join(dirs) + "<br><br><a href='/dl_top'>top</a>"

@app.route("/dl_download")
@app.route("/"+private.project_app+"/dl_download")
def download_download():
    url = request.args.get('url', '')
    fn = request.args.get('fn', '')
    proc = subprocess.Popen(["curl","-m","1800","-o",staticFolder+"/uploads/"+fn,url])
    return "<h2>start downloading...</h2><a href='/dl_ls'>ls</a>"

# upload 
@app.route("/dl_upload")
@app.route("/"+private.project_app+"/dl_upload")
def upload():
    return '''
    <form method="post" action="/dl_do_upload">
      <input type="file" name="file">
      <input type="submit" value="upload">
    </form>
'''

@app.route('/dl_do_upload', methods=['POST','GET'])
@app.route("/"+private.project_app+"/dl_do_upload", methods=['POST'])
def do_upload():
    app.logger.info("aaa")
    if 'file' not in request.files:
        return 'file not speified.'
    # file FileStorage
    # https://tedboy.github.io/flask/generated/generated/werkzeug.FileStorage.html
    fs = request.files['file']
    app.logger.info('file_name={}'.format(fs.filename))
    app.logger.info('content_type={} content_length={}, mimetype={}, mimetype_params={}'.format(
        fs.content_type, fs.content_length, fs.mimetype, fs.mimetype_params))
    fs.save(staticFolder+'/upload/'+fs.filename)


@app.route("/"+private.project_app+"/gmail_test")
def gmail_test():
    myGmail.test()
    return 'sent'

@app.route("/test")
@app.route("/"+private.project_app+"/test")
def test():
    return 'test'

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    import os
    import logging
    dirs = ["/home/sdkn104home/", "/home/sdkn104/system/log/","/home/sadakane/system/log/", "./"]
    for d in dirs:
       if os.path.exists(d):
          logdir = d
          break
    print("set logdir to " + d)
    logging.basicConfig(filename=logdir+'flask.log',level=logging.INFO)
    #logging.basicConfig(filename=logdir+'flask.log',level=logging.DEBUG)
    #app.run(host='127.0.0.1', port=8080, debug=True)
    app.run(host='0.0.0.0', port=80, debug=True) #
