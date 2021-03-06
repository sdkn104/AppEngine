from __future__ import print_function
from googleapiclient.discovery import build
from googleapiclient import errors
from httplib2 import Http
from oauth2client import file, client, tools

from email.mime.text import MIMEText
import base64
import email
import urllib.parse
import urllib.request

import private

#
# CAUTION
#  GMAIL REFRESH TOKEN would EXPIRE:
#    https://developers.google.com/identity/protocols/OAuth2
#    when expired, you need to get it again by web browser, etc.


# If modifying these scopes, delete the file CLIENT_TOKEN_FILE
SCOPES = 'https://www.googleapis.com/auth/gmail.send'
SCOPES = ['https://www.googleapis.com/auth/gmail.send','https://www.googleapis.com/auth/gmail.readonly']
CLIENT_SECRET_FILE = 'credentials/client_secret.json'
CLIENT_TOKEN_FILE = "credentials/gmail-token.json"


def get_credentials():
    # The file CLIENT_TOKEN_FILE stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    store = file.Storage(CLIENT_TOKEN_FILE)
    credentials = store.get()
    #credentials = None
    if not credentials or credentials.invalid:  # invalid does not mean access token expiration
        # Autiorization flow (need to interact with Web Browser)
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        credentials = tools.run_flow(flow, store)
        print("Storing credentials to " + CLIENT_TOKEN_FILE)
    # Delete store of credentials, to prevent refreshed token to be stored
    # This is nessesary for App Engine for read-only file system.
    credentials.set_store(None) 
    # When credentials is used to access API, if the token is expired, it receives 
    # refreshed token from server and try to save it in its store.
    print("access token expired: %r" % credentials.access_token_expired)
    return credentials

def create_message(sender, to, subject, message_text):
  """Create a message for an email.
    Return an object containing a base64url encoded email object.
  """
  message = MIMEText(message_text)
  message['to'] = to
  message['from'] = sender
  message['subject'] = subject
  byte_msg = message.as_string().encode(encoding="UTF-8")
  byte_msg_b64 = base64.urlsafe_b64encode(byte_msg)
  str_msg_b64 = byte_msg_b64.decode(encoding="UTF-8")
  return {'raw': str_msg_b64}

def send_message(service, message):
  """Send an email message.
  Args:
    service: Authorized Gmail API service instance.
    can be used to indicate the authenticated user.
    message: Message to be sent.
  Returns:
    Sent Message.
  """
  message = (service.users().messages().send(userId="me", body=message)
               .execute())
  print('Message Id: %s' % message['id'])
  return message

def triggerIFTTT(event, value1, value2, value3):
    key = private.IFTTT_key
    url = "http://maker.ifttt.com/trigger/"+urllib.parse.quote(event)+"/with/key/"+key + \
          "?value1="+urllib.parse.quote(value1)+"&value2="+urllib.parse.quote(value2)+ \
          "&value3="+urllib.parse.quote(value3)  #+" HTTP/1.1\r\n"
    #print(url)
    res = urllib.request.urlopen(url)
    status = res.getcode()
    print("IFTTT status: %s, response: %s" % (status, res.read()))

def sendGmail(sender, to, subject, message_text):
    try:
       creds = get_credentials()
       service = build('gmail', 'v1', http=creds.authorize(Http()))
       msg = create_message(sender, to, subject, message_text)
       message = send_message(service, msg)
       return message
    except Exception as e:
       import traceback
       tb = traceback.format_exc()
       #print("traceback:\n"+tb)
       print("error (%s) caught. triggering IFTTT AlertMail." % type(e))
       triggerIFTTT("AlertMail", "Failed to send mail by Gmail API in myGmail.py.", "subject: "+subject, \
                    "trace:\n"+tb)
       raise

def sendAlertMail(subject, message_text):
    sendGmail("sdkn104home@gmail.com", "sdkn104@yahoo.co.jp;sdkn104@gmail.com", subject, message_text)

# メッセージの一覧を取得
def gmail_get_messages():
    creds = get_credentials()
    service = build('gmail', 'v1', http=creds.authorize(Http()))
    # メッセージの一覧を取得
    messages = service.users().messages()
    msg_list = messages.list(userId='me', maxResults=20).execute()
    # 取得したメッセージの一覧を表示
    text = ""
    for msg in msg_list['messages']:
        topid = msg['id']
        msg = messages.get(userId='me', id=topid).execute()
        text += "-------\n"
        #print(msg['snippet']) # 要約を表示
        print("---")
        data = messages.get(userId='me', id=topid, format='raw').execute()
        raw_data = base64.urlsafe_b64decode(data['raw'])
        eml = email.message_from_bytes(raw_data)
        text += "Subject:"+eml["Subject"] + "\n"
        text += eml["From"]+ "\n"
        text += eml["To"] + "\n"
        text += eml["Date"] + "\n"
        body = ""
        for part in eml.walk(): # (4)
            if part.get_content_type() != 'text/plain': # (5)
                continue
            s = part.get_payload(decode=True)
            if isinstance(s, bytes):
                charset = part.get_content_charset() or 'iso-2022-jp' # (6)
                s = s.decode(str(charset), errors="replace")
            body += s  
        text += body + "\n"
    #print(text)
    return text

def test():
    msg = sendGmail("sdkn104home@gmail.com", "sdkn104@yahoo.co.jp;sdkn104@gmail.com", "test", "this is test")
    if msg == None:
        print("failed to send email.")

if __name__ == '__main__':
    test()
    s = gmail_get_messages()
    print(s)
