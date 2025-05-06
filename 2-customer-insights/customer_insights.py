import json

def lambda_handler(event, context):
    print("Received event:", event)
    
    # Simple response for diagnostic purposes
    response = {
        'response': {
            'actionGroup': event.get('actionGroup', 'UnknownActionGroup'),
            'function': event.get('function', 'UnknownFunction'),
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': "Hello from Lambda! This is a diagnostic response."
                    }
                }
            }
        }
    }
    
    print("Returning response:", response)
    return response
