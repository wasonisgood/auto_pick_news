# netlify/functions/hello.py
import json

def handler(event, context):
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
        },
        'body': json.dumps({
            'message': 'Hello from Python!'
        })
    }