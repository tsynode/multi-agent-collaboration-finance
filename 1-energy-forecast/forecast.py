import boto3
import json
import os

from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime

dynamodb_resource = boto3.resource('dynamodb')
dynamodb_table = os.getenv('dynamodb_table')
dynamodb_pk = os.getenv('dynamodb_pk')
dynamodb_sk = os.getenv('dynamodb_sk')
current_month = "{}/01".format(datetime.today().strftime("%Y/%m"))


def get_named_parameter(event, name):
    return next(item for item in event['parameters'] if item['name'] == name)['value']
    
def populate_function_response(event, response_body):
    return {'response': {'actionGroup': event['actionGroup'], 'function': event['function'],
                'functionResponse': {'responseBody': {'TEXT': {'body': str(response_body)}}}}}

def read_dynamodb(table_name: str, 
                   pk_field: str,
                   pk_value: str,
                   sk_field: str=None, 
                   sk_value: str=None,
                   attr_key: str=None,
                   attr_val: str=None,):
    try:

        table = dynamodb_resource.Table(table_name)
        # Create expression
        if sk_field:
            key_expression = Key(pk_field).eq(pk_value) & Key(sk_field).begins_with(sk_value)
        else:
            key_expression = Key(pk_field).eq(pk_value)

        if attr_key:
            attr_expression = Attr(attr_key).eq(attr_val)
            query_data = table.query(
                KeyConditionExpression=key_expression,
                FilterExpression=attr_expression
            )
        else:
            query_data = table.query(
                KeyConditionExpression=key_expression
            )
        
        return query_data['Items']
    except Exception:
        print(f'Error querying table: {table_name}.')

def get_forecasted_consumption(customer_id):
    return read_dynamodb(dynamodb_table, 
                         dynamodb_pk, 
                         customer_id, 
                         attr_key="kind", attr_val="forecasted")

def get_historical_consumption(customer_id):
    return read_dynamodb(dynamodb_table, 
                         dynamodb_pk, 
                         customer_id, 
                         attr_key="kind", attr_val="measured")

def get_consumption_statistics(customer_id):
    return read_dynamodb(dynamodb_table, 
                         dynamodb_pk, 
                         customer_id, 
                         dynamodb_sk, 
                         current_month)

def update_forecasting(customer_id):
    return "forecast updated for customer: {}".format(customer_id)

def lambda_handler(event, context):
    print(event)
    
    # name of the function that should be invoked
    function = event.get('function', '')

    # parameters to invoke function with
    parameters = event.get('parameters', [])
    customer_id = get_named_parameter(event, "customer_id")

    if function == 'get_forecasted_consumption':
        result = get_forecasted_consumption(customer_id)
    elif function == 'get_historical_consumption':
        result = get_historical_consumption(customer_id)
    elif function == 'get_consumption_statistics':
        result = get_consumption_statistics(customer_id)
    elif function == 'update_forecasting':
        result = update_forecasting(customer_id)
    else:
        result = f"Error, function '{function}' not recognized"

    response = populate_function_response(event, result)
    print(response)
    return response
