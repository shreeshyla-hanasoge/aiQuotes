import json
import os
import random
import boto3
import pymysql
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Database configuration
DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')

# Bedrock configuration
bedrock = boto3.client('bedrock-runtime', region_name=os.environ.get('BEDROCK_REGION', 'us-east-1'))

# Database connection management
connection = None

def get_db_connection():
    global connection
    if connection is None:
        try:
            connection = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=5
            )
            logger.info("Connected to database")
        except pymysql.MySQLError as e:
            logger.error(f"Database connection failed: {e}")
            raise e
    elif not connection.open:
         connection.ping(reconnect=True)
         
    return connection

def get_real_quote(genre):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Safe parameterized query
            sql = "SELECT text, author FROM quotes WHERE genre = %s ORDER BY RAND() LIMIT 1"
            cursor.execute(sql, (genre,))
            result = cursor.fetchone()
            
            if result:
                return {
                    "quote": result['text'],
                    "author": result['author'],
                    "source": "database"
                }
            else:
                # Fallback if no quote found for genre
                return {
                    "quote": "Success is not final, failure is not fatal: it is the courage to continue that counts.",
                    "author": "Winston Churchill",
                    "source": "fallback"
                }
    except Exception as e:
        logger.error(f"Error fetching real quote: {e}")
        return {
            "error": "Failed to fetch quote from database",
            "details": str(e)
        }

def get_ai_quote(genre, prompt=None):
    try:
        # Switch to Amazon Nova Micro
        model_id = "amazon.nova-micro-v1:0"
        logger.info(f"Attempting to invoke model: {model_id}")
        
        # Construct prompt
        user_message = f"Generate an inspirational quote about {genre}."
        if prompt:
            user_message += f" Context: {prompt}"
        user_message += "\nReturn ONLY the quote text and the author. Format: \"Quote Text\" - Author Name"

        # Nova payload format (Converse API style messages)
        body = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"text": user_message}
                    ]
                }
            ],
            "inferenceConfig": {
                "max_new_tokens": 200
            }
        }

        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(body)
        )
        
        model_response = json.loads(response["body"].read())
        # Parse Nova response
        generated_text = model_response["output"]["message"]["content"][0]["text"].strip()
        
        # Simple cleanup
        generated_text = generated_text.replace('"', '')

        return {
            "quote": generated_text,
            "author": "AI (Amazon Nova Micro)",
            "source": "bedrock"
        }

    except Exception as e:
        logger.error(f"Error generating AI quote: {e}")
        return {
            "error": "Failed to generate AI quote",
            "details": str(e)
        }

def list_models():
    try:
        # Use a new client for listing models to ensure we hit the right endpoint
        bedrock_client = boto3.client('bedrock', region_name=os.environ.get('BEDROCK_REGION', 'us-east-1'))
        response = bedrock_client.list_foundation_models()
        models = []
        for model in response['modelSummaries']:
            # Filter for text models from supported providers
            if 'TEXT' in model.get('outputModalities', []) and model['modelId'].startswith(('amazon', 'anthropic', 'meta', 'mistral', 'cohere')):
                models.append({
                    "id": model['modelId'],
                    "name": model['modelName'],
                    "status": model['modelLifecycle']['status']
                })
        return {"models": models}
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return {"error": f"Failed to list models: {str(e)}"}

def get_quote(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        body = {}
        # Handle API Gateway/Function URL event (body is a string)
        if 'body' in event:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
        # Handle direct invocation (event is the body)
        else:
            body = event
            
        quote_type = body.get('type', 'real') # Default to real
        genre = body.get('genre', 'motivation')
        prompt = body.get('prompt')

        if quote_type == 'ai':
            response_data = get_ai_quote(genre, prompt)
        elif quote_type == 'list_models':
            response_data = list_models()
        else:
            response_data = get_real_quote(genre)

        return {
            "statusCode": 200,
            "body": json.dumps(response_data),
            "headers": {
                "Content-Type": "application/json"
            }
        }

    except Exception as e:
        logger.error(f"Handler error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal Server Error", "details": str(e)})
        }
