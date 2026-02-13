# Manual Deployment Instructions

Due to sandbox restrictions, please run the following commands in your local terminal to deploy the project.

## Prerequisites
1.  Ensure you have AWS credentials configured (`aws configure` or env vars).
2.  Ensure you have **Docker** running (required for building Python layers).

## Deployment Steps

1.  **Install Dependencies**
    ```bash
    npm install
    ```

2.  **Deploy**
    ```bash
    npx serverless deploy
    ```

## Post-Deployment
Once deployed, you will see an output like:
```
endpoints:
  POST - https://xxxxxx.execute-api.us-east-1.amazonaws.com/quotes
```
Copy this URL to test the API.
