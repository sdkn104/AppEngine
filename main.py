#
# Main of AppEngine service
#

from flask import Flask, request, redirect, make_response

import requests
import private

import myStock

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)

nodeServiceHost = "node-app-dot-fresh-catwalk-335010.an.r.appspot.com"
gceHost = "35.203.132.149:80"

def loginCheck():
    html = "<form method='POST'>User Name<input type='text' name=username><br>Password<input type='password' name='password'><br><input type='submit'></form>"
    if request.method == "POST" and "username" in request.form and "password" in request.form and request.form['username'] == private.app_username and request.form['password'] == private.app_password:
        return None
    else:
        return html

@app.route("/", methods=["GET","POST"])
def hello():
    return 'Hello World! This page is created by App Engine service2.<br><a href="/top">top</a><br>'

@app.route("/top", methods=["GET","POST"])
def top():
    h = loginCheck()
    if h is not None:
        return h
    return '''
        <a href='/dl_top'>download</a><br>
        <a href='/{project_app}/imports'>import kakeibo/unyou</a><br>
        <a href='{nodeServiceHost}'>top nodeJS</a><br>
    '''.format(nodeServiceHost=nodeServiceHost, project_app=private.project_app)


# imports
@app.route("/"+private.project_app+"/imports", methods=['GET', 'POST'])
def imports():
    return '''
        <!DOCTYPE html>
        <html>
        <h2>KAKEIBO/UNYOU DATA FILE UPLOAD</h2>
        <h3>KAKEIBO CSV</h3>
        <form action="/{project_app}/kakeiboCsv" method="POST" enctype="multipart/form-data">
            <input type="file" name="body">
            <input type="submit">
        </form>
        <h3>UNYOU CSV</h3>
        <form action="/{project_app}/unyouCsv" method="POST" enctype="multipart/form-data">
            <input type="file" name="body">
            <input type="submit">
        </form>
        </html>
    '''.format(nodeServiceHost=nodeServiceHost, project_app=private.project_app)

# receive Kakeibo HTML 
@app.route("/"+private.project_app+"/kakeiboHtml", methods=['POST'])
def kakeiboHtml():
    data = request.form['body']
    import importKakeiboCsv
    import myGSpread
    values = importKakeiboCsv.getDataHtml(data)
    myGSpread.appendRows(values,"家計簿", "検索")
    return make_response(str(values),[("Content-Type","text/plain; charset=utf-8")])
    
# receive Kakeibo CSV
@app.route("/"+private.project_app+"/kakeiboCsv", methods=['POST'])
def kakeiboCsv():
    file = request.files['body']
    csv = file.read()
    print(csv)
    import importKakeiboCsv
    import myGSpread
    values = importKakeiboCsv.getDataCsv(csv)
    myGSpread.appendRows(values,"家計簿", "検索")
    return make_response(str(values),[("Content-Type","text/plain; charset=utf-8")])
    
# receive unyou HTML 
@app.route("/"+private.project_app+"/unyouHtml", methods=['POST'])
def unyouHtml():
    data = request.form['body']
    import importStockCsv
    import myGSpread
    values = importStockCsv.getDataHtml(data)
    myGSpread.appendRows(values,"運用履歴", "data")
    return make_response(str(values),[("Content-Type","text/plain; charset=utf-8")])

# receive unyou csv 
@app.route("/"+private.project_app+"/unyouCsv", methods=['POST'])
def unyouCsv():
    data = request.form['body']
    import importStockCsv
    import myGSpread
    values = importStockCsv.getDataHtml(data)
    myGSpread.appendRows(values,"運用履歴", "data")
    return make_response(str(values),[("Content-Type","text/plain; charset=utf-8")])

# send stock (moved from server)
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


@app.route("/insertBQ")
def insertBQ():
    import myBigQuery
    table = request.args.get('table', '')
    value1 = request.args.get('value1', '')
    value2 = request.args.get('value2', '')
    value3 = request.args.get('value3', '')
    value4 = request.args.get('value4', '')
    myBigQuery.loadBigQuery(table, [[value1, value2, value3, value4]])
    import gc
    gc.collect()
    return 'done inserting to '+table+", ("+value1+", "+value2+", "+value3+", "+value4+")"

@app.route("/gmail")
def gmail():
    import myGmail
    addr_to = request.args.get('to', '')
    subject = request.args.get('subject', '')
    body = request.args.get('body', '')
    if addr_to == "":
        addr_to = "sdkn104@yahoo.co.jp"
    myGmail.sendGmail("sdkn104home@gmail.com", addr_to, subject, body)
    return 'done sending gmail '+subject+" to "+addr_to

# redirect to AppEngine node-app service
@app.route('/node/<path:path>', methods=['POST','GET'])
def catch_node(path):
    url = "https://" + nodeServiceHost + (request.script_root + request.full_path).replace("/node","",1)
    print("redirecting to "+url)
    return redirect(url)

# transfer to GCE
@app.route('/xxxxxx/<path:path>', methods=['POST','GET'])
def catch_all_private(path):    
    url = "http://" + gceHost + request.script_root + request.full_path
    print("transferring to "+url)
    if request.method == "GET":
        r = requests.get(url)
    if request.method == "POST":
        r = requests.post(url, data=request.form)
    return make_response(r.content, r.status_code)

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
