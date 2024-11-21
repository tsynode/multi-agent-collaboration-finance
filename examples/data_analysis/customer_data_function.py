## Be sure to have IAM permission to save and retrieve files from the agent file store
## folder in the bucket. Here is a sample policy:

# {
#     "Version": "2012-10-17",
#     "Statement": [
#         {
#             "Sid": "ListBucketWithPrefix",
#             "Effect": "Allow",
#             "Action": "s3:ListBucket",
#             "Resource": "arn:aws:s3:::*",
#             "Condition": {
#                 "StringLike": {
#                     "s3:prefix": [
#                         "AGENT_FILE_STORE/*",
#                           "CODE_INTERP_FILE_STORE/*"
#                     ]
#                 }
#             }
#         },
#         {
#             "Sid": "ReadWriteObjectsWithPrefix",
#             "Effect": "Allow",
#             "Action": [
#                 "s3:GetObject",
#                 "s3:PutObject"
#             ],
#             "Resource": "arn:aws:s3:::*/AGENT_FILE_STORE/*"
#         }
#     ]
# }

import json
import boto3
import pprint
from botocore.config import Config
import os

FILE_STORAGE_FOLDER = 'CODE_INTERP_FILE_STORE'
long_invoke_time_config = Config(read_timeout=600)

def get_named_parameter(event, name):
    return next(item for item in event['parameters'] if item['name'] == name)['value']
    
def populate_function_response(event, response_body):
    return {'response': {'actionGroup': event['actionGroup'], 'function': event['function'],
                'functionResponse': {'responseBody': {'TEXT': {'body': str(response_body)}}}}}

def cp_tmp_file_to_s3(bucket: str, file_name: str, tmp_file_path: str, session_id: str):
    print(f"Save to file in bucket: {bucket}, name: {file_name}, from: {tmp_file_path}")

    # Get the contents of a file from the tmp_file_path
    with open(tmp_file_path, 'rb') as tmp_file:
        contents = tmp_file.read()

    # use boto3 to save contents to file in bucket
    s3 = boto3.resource('s3', config=long_invoke_time_config)
    key = f"{FILE_STORAGE_FOLDER}/{session_id}/{file_name}"
    print(f"Saving file at key: {key}, in s3 bucket {bucket}...")
    response = s3.Object(bucket, key).put(Body=contents)
    print(response)
    return

def customer_data_lookup(query, bucket, session_id):

    results_file = 'query_results.csv'
    dest_s3_file = {'bucket': bucket, 'key': results_file}

    # make a customers.csv with 2 rows and 2 columns. first row for
    # customer ABC, second row for customer DEF. each row should have a customer
    # name and a total sales year to date. csv should have a header.

    tmp_file_path = f"/tmp/{results_file}"
    with open(tmp_file_path, 'w') as temp_file:
        temp_file.write('customer,total_sales_ytd\n')
        temp_file.write('ABC,100\n')
        temp_file.write('DEF,200\n')
        temp_file.write('GHI,300\n')
        temp_file.write('JKL,400\n')

    cp_tmp_file_to_s3(dest_s3_file['bucket'], dest_s3_file['key'], tmp_file_path, session_id)

    print(f"Saving query results under session: {session_id}, with key: {dest_s3_file['key']} on bucket: {dest_s3_file['bucket']}")
    return f"Saved query results to filename {dest_s3_file['key']}, using the bucket you specified: {dest_s3_file['bucket']}"

def get_named_parameter(event, name):
    return next(item for item in event['parameters'] if item['name'] == name)['value']
    
def populate_function_response(event, response_body):
    return {'response': {'actionGroup': event['actionGroup'], 'function': event['function'],
                'functionResponse': {'responseBody': {'TEXT': {'body': str(response_body)}}}}}

def lambda_handler(event, context):
    print(event)
    
    function = event['function']
    session_id = event['sessionId']

    if function == "customer_data_lookup":
        query = get_named_parameter(event, 'query')
        if not query:
            raise Exception("Missing mandatory parameter: query")
        
        results_s3_bucket = get_named_parameter(event, 'results_s3_bucket')

        result = customer_data_lookup(query, results_s3_bucket, session_id)
    else:
        raise Exception(f"Unrecognized function: {function}")

    response = populate_function_response(event, result)
    print(response)
    return response
