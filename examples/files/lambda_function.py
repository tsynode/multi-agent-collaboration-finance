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
#                         "AGENT_FILE_STORE/*"
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
from botocore.config import Config

long_invoke_time_config = Config(read_timeout=600)

FILE_STORAGE_FOLDER = 'AGENT_FILE_STORE'

def get_named_parameter(event, name):
    return next(item for item in event['parameters'] if item['name'] == name)['value']
    
def populate_function_response(event, response_body):
    return {'response': {'actionGroup': event['actionGroup'], 'function': event['function'],
                'functionResponse': {'responseBody': {'TEXT': {'body': str(response_body)}}}}}

def save_file(bucket: str, file_name: str, contents: str, session_id: str):
    print(f"Save file called: {bucket}, {file_name}, {contents}")
    # use boto3 to save contents to file in bucket
    s3 = boto3.resource('s3', config=long_invoke_time_config)
    response = s3.Object(bucket, f'{FILE_STORAGE_FOLDER}/{session_id}/{file_name}').put(Body=contents)
    print(response)
    return

def get_file(bucket: str, file_name: str, session_id: str) -> str:
    print(f"Get file called: {bucket}, {file_name}")
    # use boto3 to get file from bucket
    s3 = boto3.resource('s3', config=long_invoke_time_config)
    response = s3.Object(bucket, f'{FILE_STORAGE_FOLDER}/{session_id}/{file_name}').get()
    contents = response['Body'].read().decode('utf-8')
    return str(contents)

def lambda_handler(event, context):
    print(event)
    
    function = event['function']
    session_id = event['sessionId']

    bucket = get_named_parameter(event, 'bucket')
    file_name = get_named_parameter(event, 'file_name')

    if function == 'save_file':
        contents = get_named_parameter(event, 'contents')
        save_file(bucket, file_name, contents, session_id)
        result = f"Stored contents to s3://{bucket}/{FILE_STORAGE_FOLDER}/{session_id}/{file_name}. Contents were: {contents}"

    elif function == 'get_file':
        contents = get_file(bucket, file_name, session_id)
        result = f"Retrieved contents from s3://{bucket}/{FILE_STORAGE_FOLDER}/{session_id}/{file_name}. Contents were: {contents}"
    
    else:
        result = f"Invalid function sent to Lambda: {function}"

    response = populate_function_response(event, result)
    print(response)
    return response