#!/usr/bin/python3

#
# upload data to bigquery
#

from google.cloud import bigquery
import os

bqJsonPath = ["/home/sdkn104/system/etc/BigQueryKey.json","/home/sadakane/system/etc/BigQueryKey.json","credentials/BigQueryKey.json"]
for json in bqJsonPath:
  if os.path.exists(json):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = json
    print("set credential to " + json)


# values = 2-dim array = [[value1, value2, ...], [value1, value2, ...], ... ]
def triggerBigQuery(table, values):
  try:
    client = bigquery.Client()

    dataset_id = 'HOME_IoT'  # replace with your dataset ID
    table_id = table         # replace with your table ID
    table_ref = client.dataset(dataset_id).table(table_id)
    table = client.get_table(table_ref)  # API request

    errors = client.insert_rows(table, values)  # API request
    #print(errors)
    assert errors == []  # exception occur, so response status >= 300
    print("{'status':'success'}")
  except Exception as e:
    import sys
    m = str(sys.exc_info()[0])  #e.args
    print("Exception occur!!\n"+m)
    raise


#if __name__ == "__main__":
#    triggerBigQuery(table, [value1, value2, value3, value4])

