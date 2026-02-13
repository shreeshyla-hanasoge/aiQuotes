import boto3
import json

client = boto3.client('lambda', region_name='us-east-1')
FUNCTION_NAME = 'aiQuotes-getQuote'

payload = {
    "type": "ai",
    "genre": "technology",
    "prompt": "The future of coding"
}

try:
    response = client.invoke(
        FunctionName=FUNCTION_NAME,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    response_payload = json.loads(response['Payload'].read())
    print(json.dumps(response_payload, indent=2))
except Exception as e:
    print(e)
