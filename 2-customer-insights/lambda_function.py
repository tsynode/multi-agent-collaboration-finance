import boto3
import json
import os

from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime
from decimal import Decimal

dynamodb_resource = boto3.resource('dynamodb')
dynamodb_table = os.getenv('dynamodb_table')
dynamodb_pk = os.getenv('dynamodb_pk')
dynamodb_sk = os.getenv('dynamodb_sk')


def get_named_parameter(event, name):
    try:
        return next(item for item in event['parameters'] if item['name'] == name)['value']
    except:
        return None
    
def populate_function_response(event, response_body):
    return {'response': {'actionGroup': event['actionGroup'], 'function': event['function'],
                'functionResponse': {'responseBody': {'TEXT': {'body': str(response_body)}}}}}


def lambda_handler(event, context):
    print(event)
    
    # name of the function that should be invoked
    function = event.get('function', '')

    # parameters to invoke function with
    parameters = event.get('parameters', [])
    customer_id = get_named_parameter(event, "customer_id")

    # Simple diagnostic response for testing
    result = f"Hello from Lambda! Function: {function}, Customer ID: {customer_id}"

    response = populate_function_response(event, result)
    print(response)
    return response
