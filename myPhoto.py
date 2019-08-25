"""
Shows basic usage of the Photos v1 API.

Creates a Photos v1 API service and prints the names and ids of the last 10 albums
the user has access to.
"""
from apiclient.discovery import build
from google_auth_oauthlib import flow
from google.oauth2.credentials import Credentials
import google.auth.transport.requests

import os
import datetime
import pickle
import requests

credPath = ["/home/sdkn104/system/etc","/home/sadakane/system/etc",
    "C:/Users/sdkn1/AppData/Local/Google/Cloud SDK/appengine/service/credentials", 
    "credentials", "."]
credFile = "client_secret_sdkn104gmail.json"
for f in [p+"/"+credFile for p in credPath]:
  if os.path.exists(f):
    cred = f
    print("set credential to " + cred)
    break

credPickle = cred + ".token.pickle"

# Setup the Photo v1 API
SCOPES = 'https://www.googleapis.com/auth/photoslibrary.readonly'


# TODO: Uncomment the line below to set the `launch_browser` variable.
launch_browser = True
#
# The `launch_browser` boolean variable indicates if a local server is used
# as the callback URL in the auth flow. A value of `True` is recommended,
# but a local server does not work if accessing the application remotely,
# such as over SSH or from a remote Jupyter notebook.



def printCred(creds):
    info = { 
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes,
        'expiry': creds.expiry.isoformat(),
    }
    print(info)


# ref https://developers.google.com/drive/api/v3/quickstart/python
def getCredential(clientSecretJson, scopes, credPickle):
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(credPickle):
        with open(credPickle, 'rb') as token:
            creds = pickle.load(token)
        print("read credential pickle")
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("expired. refresh....")
            creds.refresh(google.auth.transport.requests.Request())
        else:
            appflow = flow.InstalledAppFlow.from_client_secrets_file(clientSecretJson, scopes)
            if launch_browser:
                appflow.run_local_server()
            else:
                appflow.run_console()
            creds = appflow.credentials
        # Save the credentials for the next run
        with open(credPickle, 'wb') as token:
            pickle.dump(creds, token)
    printCred(creds)
    return creds



creds = getCredential(cred, SCOPES, credPickle)
service = build('photoslibrary', 'v1', credentials=creds)

#https://developers.google.com/photos/library/guides/overview

# Call the Photo v1 API
#https://stackoverflow.com/questions/50573196/access-google-photo-api-with-python-using-google-api-python-client

nextPageToken = ''
url = None
for i in range(100):
    #results = service.mediaItems().list(pageSize=5, pageToken=nextPageToken).execute()
    results = service.mediaItems().list(pageSize=100, pageToken=nextPageToken).execute()
    items = results.get('mediaItems', [])
    if not items:
        print('No mediaItem found.')
    else:
        print('MediaItems:')
        for item in items:  
            print('{0} ({1})'.format(item['filename'], item['id']))
            print(item)
            meta = item['mediaMetadata']
            #url = item['baseUrl']+"=w"+meta['width']+"-h"+meta['height']+"-d"
            if item['filename'] == "IMG_20190729_193003.jpg":
                url = item['baseUrl'] #+"=d"
            print(url)
    nextPageToken = results.get('nextPageToken', '')
    if nextPageToken == '':
      break

response = requests.get(url)
print(response.status_code)
print(response.headers)
#print(response.content)

with open("./out.jpg","wb") as f:
  f.write(response.content)



