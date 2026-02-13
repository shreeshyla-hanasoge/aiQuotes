import boto3
import json

bedrock = boto3.client('bedrock', region_name='us-east-1')

try:
    response = bedrock.list_foundation_models()
    print("Available Models:")
    for model in response['modelSummaries']:
        # Filter for text models and Amazon/Anthropic
        if 'TEXT' in model.get('outputModalities', []) and model['modelId'].startswith(('amazon', 'anthropic')):
            print(f"- {model['modelId']} ({model['modelName']}) - Status: {model['modelLifecycle']['status']}")
except Exception as e:
    print(f"Error listing models: {e}")
