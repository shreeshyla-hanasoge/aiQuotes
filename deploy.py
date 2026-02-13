import boto3
import json
import zipfile
import os
import shutil
import subprocess
import time
import logging

# Configuration
REGION = 'us-east-1'
FUNCTION_NAME = 'aiQuotes-getQuote'
LAYER_NAME = 'aiQuotes-dependencies'
ROLE_NAME = 'aiQuotes-LambdaRole'
DB_HOST = os.environ.get('DB_HOST', '144.24.134.189')
DB_USER = os.environ.get('DB_USER', 'free_application_user')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'noquotesDevUse1!')
DB_NAME = os.environ.get('DB_NAME', 'aiquotes')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('deploy')

# Initialize Boto3 clients
lambda_client = boto3.client('lambda', region_name=REGION)
iam_client = boto3.client('iam', region_name=REGION)

def create_iam_role():
    """Creates IAM role for Lambda if it doesn't exist."""
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        role = iam_client.get_role(RoleName=ROLE_NAME)
        logger.info(f"Role {ROLE_NAME} already exists. ARN: {role['Role']['Arn']}")
        return role['Role']['Arn']
    except iam_client.exceptions.NoSuchEntityException:
        logger.info(f"Creating role {ROLE_NAME}...")
        role = iam_client.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        
        # Attach policies
        policies = [
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
            "arn:aws:iam::aws:policy/AmazonBedrockFullAccess" # Simplified for demo
        ]
        
        for policy_arn in policies:
            iam_client.attach_role_policy(
                RoleName=ROLE_NAME,
                PolicyArn=policy_arn
            )
        
        logger.info("Role created. Waiting for propagation...")
        time.sleep(10) # Wait for role to be ready
        return role['Role']['Arn']

import sys

def create_layer_zip():
    """Installs requirements and zips them for Lambda Layer."""
    build_dir = "layer_build"
    python_dir = os.path.join(build_dir, "python")
    
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    
    os.makedirs(python_dir)
    
    logger.info("Installing requirements...")
    # Use the same python executable to run pip
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-r", "requirements.txt", 
        "-t", python_dir
    ])
    
    zip_filename = "layer.zip"
    logger.info(f"Zipping layer to {zip_filename}...")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, build_dir)
                zipf.write(file_path, arcname)
                
    # Cleanup
    shutil.rmtree(build_dir)
    return zip_filename

def create_code_zip():
    """Zips the handler code."""
    zip_filename = "code.zip"
    logger.info(f"Zipping code to {zip_filename}...")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write("handler.py")
    return zip_filename

def deploy_layer(zip_file):
    """Publishes a new version of the Lambda Layer."""
    logger.info(f"Publishing layer {LAYER_NAME}...")
    with open(zip_file, 'rb') as f:
        response = lambda_client.publish_layer_version(
            LayerName=LAYER_NAME,
            Content={'ZipFile': f.read()},
            CompatibleRuntimes=['python3.12'],
            CompatibleArchitectures=['arm64']
        )
    logger.info(f"Layer published: {response['LayerVersionArn']}")
    return response['LayerVersionArn']

def deploy_function(role_arn, layer_arn, zip_file):
    """Creates or updates the Lambda function."""
    with open(zip_file, 'rb') as f:
        code_content = f.read()

    try:
        logger.info(f"Checking if function {FUNCTION_NAME} exists...")
        lambda_client.get_function(FunctionName=FUNCTION_NAME)
        
        logger.info("Updating function code...")
        lambda_client.update_function_code(
            FunctionName=FUNCTION_NAME,
            ZipFile=code_content,
            Architectures=['arm64']
        )
        
        # Wait for update to complete
        logger.info("Waiting for code update to complete...")
        waiter = lambda_client.get_waiter('function_updated')
        waiter.wait(FunctionName=FUNCTION_NAME)
        
        logger.info("Updating function configuration...")
        lambda_client.update_function_configuration(
            FunctionName=FUNCTION_NAME,
            Role=role_arn,
            Handler='handler.get_quote',
            Runtime='python3.12',
            Layers=[layer_arn],
            Environment={
                'Variables': {
                    'DB_HOST': DB_HOST,
                    'DB_USER': DB_USER,
                    'DB_PASSWORD': DB_PASSWORD,
                    'DB_NAME': DB_NAME,
                    'BEDROCK_REGION': REGION
                }
            }
        )
        logger.info("Function updated.")
        
    except lambda_client.exceptions.ResourceNotFoundException:
        logger.info("Creating function...")
        lambda_client.create_function(
            FunctionName=FUNCTION_NAME,
            Runtime='python3.12',
            Role=role_arn,
            Handler='handler.get_quote',
            Code={'ZipFile': code_content},
            Layers=[layer_arn],
            Architectures=['arm64'],
            Environment={
                'Variables': {
                    'DB_HOST': DB_HOST,
                    'DB_USER': DB_USER,
                    'DB_PASSWORD': DB_PASSWORD,
                    'DB_NAME': DB_NAME,
                    'BEDROCK_REGION': REGION
                }
            },
            Timeout=10,
            MemorySize=128
        )
        logger.info("Function created.")

def create_function_url():
    """Creates or updates a public Function URL with CORS."""
    cors_config = {
        'AllowOrigins': ['*'],
        'AllowMethods': ['*'],
        'AllowHeaders': ['content-type'],
        'MaxAge': 86400
    }
    
    url = ""
    try:
        response = lambda_client.create_function_url_config(
            FunctionName=FUNCTION_NAME,
            AuthType='NONE',
            Cors=cors_config
        )
        logger.info(f"Function URL created: {response['FunctionUrl']}")
        url = response['FunctionUrl']
    except lambda_client.exceptions.ResourceConflictException:
        logger.info("Function URL already exists. Updating configuration...")
        response = lambda_client.update_function_url_config(
            FunctionName=FUNCTION_NAME,
            AuthType='NONE',
            Cors=cors_config
        )
        logger.info(f"Function URL updated: {response['FunctionUrl']}")
        url = response['FunctionUrl']
    
    # Add permission for public access
    try:
        lambda_client.add_permission(
            FunctionName=FUNCTION_NAME,
            StatementId='FunctionURLAllowPublicAccess',
            Action='lambda:InvokeFunctionUrl',
            Principal='*',
            FunctionUrlAuthType='NONE'
        )
        logger.info("Added permission for public access")
    except lambda_client.exceptions.ResourceConflictException:
        logger.info("Public access permission already exists")
        
    
    return url

# Initialize API Gateway Client
apigw_client = boto3.client('apigatewayv2', region_name=REGION)
API_NAME = 'aiQuotes-API'

def deploy_api_gateway():
    """Deploys HTTP API Gateway for public access."""
    # 0. Get Function ARN
    fn = lambda_client.get_function(FunctionName=FUNCTION_NAME)
    fn_arn = fn['Configuration']['FunctionArn']

    # 1. Create/Get API
    logger.info("Configuring API Gateway...")
    api_id = None
    api_endpoint = None
    
    # Check if API exists (simplified by creating new one for reliability in this script context)
    # Ideally we would list APIs and find by name, but for now we create/update logic via name uniqueness isn't built-in easily
    # We will create a new one to guarantee it works. User can clean up old ones manually.
    try:
        api = apigw_client.create_api(
            Name=API_NAME,
            ProtocolType='HTTP',
            CorsConfiguration={
                'AllowOrigins': ['*'],
                'AllowMethods': ['POST', 'OPTIONS'],
                'AllowHeaders': ['content-type'],
                'MaxAge': 86400
            }
        )
        api_id = api['ApiId']
        api_endpoint = api['ApiEndpoint']
        logger.info(f"API Gateway Created: {api_id}")
    except Exception as e:
        logger.error(f"Error creating API: {e}")
        return None

    # 2. Create Integration
    try:
        integration = apigw_client.create_integration(
            ApiId=api_id,
            IntegrationType='AWS_PROXY',
            IntegrationUri=fn_arn,
            PayloadFormatVersion='2.0'
        )
        integration_id = integration['IntegrationId']
    except Exception as e:
        logger.error(f"Error creating integration: {e}")
        return None

    # 3. Create Route
    try:
        apigw_client.create_route(
            ApiId=api_id,
            RouteKey='POST /',
            Target=f'integrations/{integration_id}'
        )
    except Exception as e:
        logger.error(f"Error creating route: {e}")

    # 4. Create Stage
    try:
        apigw_client.create_stage(
            ApiId=api_id,
            StageName='$default',
            AutoDeploy=True
        )
    except apigw_client.exceptions.ConflictException:
        pass

    # 5. Add Permission to Lambda
    try:
        lambda_client.add_permission(
            FunctionName=FUNCTION_NAME,
            StatementId=f'APIGatewayInvoke_{api_id}',
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=f"arn:aws:execute-api:{REGION}:{boto3.client('sts').get_caller_identity()['Account']}:{api_id}/*/*"
        )
    except lambda_client.exceptions.ResourceConflictException:
        pass
    except Exception as e:
        logger.error(f"Error adding permission: {e}")

    return api_endpoint

def main():
    logger.info("Starting deployment...")
    
    # 1. IAM Role
    role_arn = create_iam_role()
    
    # 2. Prepare Zips
    layer_zip = create_layer_zip()
    code_zip = create_code_zip()
    
    # 3. Deploy Layer
    layer_arn = deploy_layer(layer_zip)
    
    # 4. Deploy Function
    deploy_function(role_arn, layer_arn, code_zip)
    
    # 5. Public Endpoint (API Gateway)
    # Note: We are switching from Function URL to API Gateway due to account restrictions on public Function URLs.
    url = deploy_api_gateway()
    
    # Cleanup
    os.remove(layer_zip)
    os.remove(code_zip)
    
    print("\n" + "="*50)
    print(f"Deployment Complete!")
    print(f"API Endpoint: {url}")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
