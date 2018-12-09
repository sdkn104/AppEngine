
import os

import gspread
from oauth2client.service_account import ServiceAccountCredentials

credPath = ["/home/sdkn104/system/etc","/home/sadakane/system/etc",
    "C:/Users/sdkn1/AppData/Local/Google/Cloud SDK/appengine/service/credentials", 
    "credentials", "."]
for f in [p+"/BigQueryKey.json" for p in credPath]:
  if os.path.exists(f):
    cred = f
    print("set credential to " + cred)
    break

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

def insertRows(values, spreadsheet, worksheet, start_row=0):
  """insert rows before the row number start_row.
     if start_row = 0, insert after the last non-blank row.
     values is a list of lists.
  """
  credentials = ServiceAccountCredentials.from_json_keyfile_name(cred, scope)
  gc = gspread.authorize(credentials)

  wks = gc.open(spreadsheet).worksheet(worksheet)
  if start_row <= 0:
    start_row = len(wks.get_all_values()) + 1 - start_row
  if start_row + len(values) - 1 > wks.row_count: 
    wks.add_rows(start_row + len(values) - 1 - wks.row_count)
  # insert  # to speed up, use values_update()
  values.reverse()
  for row in values:
    wks.insert_row(row, start_row)

def appendRows(values, spreadsheet, worksheet):
  """append rows to the last table in the worksheet.
     values is a list of lists.
  """
  credentials = ServiceAccountCredentials.from_json_keyfile_name(cred, scope)
  gc = gspread.authorize(credentials)

  ss = gc.open(spreadsheet)
  range_ = "'"+worksheet+"'"
  value_input_option = 'RAW'
  insert_data_option = 'INSERT_ROWS'
  value_range_body = {
    "range": range_,
    "majorDimension": "ROWS",
    "values": values
  }
  response = ss.values_append(range=range_, 
                    params={"valueInputOption":value_input_option, "insertDataOption":insert_data_option}, 
                    body=value_range_body)  
  #import pprint as pp
  #pp.pprint(response)

if __name__ == "__main__":
  appendRows([["2018-11-21",2],["2018-11-21T01:02:03+09:00",2],["20181121T010203Z",4],[5,6]], "Cloud", "test")
  print("done nothing")
  