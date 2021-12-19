#!/usr/bin/python3

#
# access to bigquery
#

import os
import io
import csv
from google.cloud import bigquery  # require abount 50MB memory

credPath = ["/home/sdkn104/system/etc","/home/sdkn104dev/system/etc","/home/sadakane/system/etc",
    "C:/Users/sdkn1/AppData/Local/Google/Cloud SDK/appengine/service/credentials", 
    "credentials", "."]
for f in [p+"/BigQueryKey.json" for p in credPath]:
  if os.path.exists(f):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f
    print("set credential to " + f)
    break


# query to BigQuery and return DataFrame
def queryBigQuery(sql):
    client = bigquery.Client()
    query_job = client.query(sql)  # API request
    rows = query_job.result()  # Waits for query to finish
    #print(rows.schema)
    df = rows.to_dataframe()
    return df
    

# Upload data to BigQuery by streaming (fast but charged)
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

# Upload data to BigQuery by Job
# records = [ [r1c2, r1c2, r1c3]], [..], ]
# records = { colname:[val1,val2, ..], ..}
# records = { colname:{ rowname:val1,rowname:val2, ..}, ..}
def loadBigQuery(table, records, asyn=False):
    client = bigquery.Client()
    dataset_id = 'HOME_IoT'  # replace with your dataset ID
    table_id = table         # replace with your table ID
    dataset_ref = client.dataset(dataset_id)
    table_ref = dataset_ref.table(table_id)
    table = client.get_table(table_ref)  # API request

    # convert to CSV
    with io.StringIO("", newline='') as csv_io:
        csvWriter = csv.writer(csv_io, quoting=csv.QUOTE_MINIMAL)
                      # csv.QUOTE_MINIMAL, csv.QUOTE_NONNUMERIC, csv.QUOTE_ALL, csv.QUOTE_NONE
        #print(records)
        csvWriter.writerows(records)
        csv_str = csv_io.getvalue()
    #print(csv_str)

    # Load Job
    job_config = bigquery.LoadJobConfig()
    job_config.source_format = 'CSV'
    job_config.skip_leading_rows = 0
    job_config.autodetect = False
    job_config.allow_quoted_newlines = True
    job_config.allow_jagged_rows = True  # allow missing columns in csv
    job_config.ignore_unknown_values = True # Ignore extra values not represented in the table schema
    csv_bin = csv_str.encode('utf8') 
    with io.BytesIO(csv_bin) as csv_bio:
        job = client.load_table_from_file(file_obj=csv_bio, destination=table_ref, job_config=job_config)
    if not asyn:
      job.result()  # Waits for table load to complete.
      assert job.state == 'DONE'
    #print(job.state)

if __name__ == "__main__":
    #triggerBigQuery(table, [value1, value2, value3, value4])
    #import datetime
    #loadBigQuery("test_csv", [[datetime.datetime.now(),"b"],[55,3.4]])
    r = queryBigQuery("select *  FROM `fresh-catwalk-335010.HOME_IoT.test_csv`")    
    print(r)
    print("done")
