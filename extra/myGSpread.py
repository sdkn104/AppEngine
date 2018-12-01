
import os

import gspread
from oauth2client.service_account import ServiceAccountCredentials

credPath = ["/home/sdkn104/system/etc/GSpread.json","/home/sadakane/system/etc/GSpread.json","credentials/GSpread.json", "./GSpread.json"]
for json in credPath:
  if os.path.exists(json):
    cred = json
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

if __name__ == "__main__":
  #insertRows([["2018-11-21",2],["2018-11-21T01:02:03+09:00",2],["20181121T010203Z",4],[5,6]], "Cloud", "test", 0)
  print("done nothing")
  
