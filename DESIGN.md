# aiQuotes - Serverless Inspirational Quotes API

## Project Overview
aiQuotes is a serverless API built on AWS that provides inspirational quotes. It serves two main functions:
1.  **Real Quotes**: Retrieving curated quotes from famous personalities based on genre.
2.  **AI Generated Quotes**: Creating unique, context-aware inspirational quotes using Generative AI based on user prompts.

## Architecture

### Infrastructure Components
The project leverages a fully serverless architecture on AWS for scalability and cost efficiency.

1.  **API Gateway (HTTP API)**
    *   **Role**: Entry point for all client requests. Handles routing, throttling, and basic validation.
    *   **Why**: HTTP API is cheaper and faster than REST API for serverless workloads.

2.  **AWS Lambda (Python 3.12)**
    *   **Role**: The backend logic.
        *   `GetQuote`: Main handler.
        *   Parses request (Real vs. AI, Genre vs. Prompt).
        *   Interacts with MySQL database or AI service.
    *   **Optimization**:
        *   Use AWS Graviton (ARM64) architecture for ~20% cost savings.
        *   **Lambda Layers**: Dependencies (e.g., `pymysql`) are packaged in a separate layer to keep the function code clean and deployment fast.

3.  **MySQL Database**
    *   **Role**: Storage for "Real" quotes and caching common AI responses.
    *   **Connection**: Lambda connects via `pymysql`.
    *   **Schema**: `quotes` table with columns `id`, `genre`, `text`, `author`.

4.  **AWS Bedrock (Cheapest Option)**
    *   **Role**: Generative AI engine.
    *   **Model**: **Amazon Titan Text Lite** (or Express).
    *   **Why**: Extremely low cost ($0.00015/1k input, $0.0002/1k output).
    *   **Alternative**: Claude 3 Haiku for higher quality at slightly higher cost.

### Workflow

1.  **Request**: User sends `POST /quotes`
    ```json
    {
      "type": "ai", // or "real"
      "genre": "motivation",
      "prompt": "For a software engineer struggling with bugs" // optional, used if type is ai
    }
    ```
2.  **Routing**: API Gateway routes to Lambda.
3.  **Processing (Lambda)**:
    *   **If Type = "real"**:
        *   Query MySQL for `genre`.
        *   Select a random quote from the result.
    *   **If Type = "ai"**:
        *   Construct prompt for AWS Bedrock.
        *   Invoke Bedrock Model.
        *   Parse and format response.
4.  **Response**: Return JSON to client.

## Cost Effective Plan

### 1. Compute (AWS Lambda)
*   **Free Tier**: 400,000 GB-seconds per month.
*   **Strategy**:
    *   Use **ARM64** architecture.
    *   Use **Lambda Layers** for efficient dependency management.

### 2. Database (MySQL)
*   Assuming existing infrastructure as per user request.

### 3. AI (AWS Bedrock)
*   **Cost**: Pricing is per 1,000 input/output tokens.
*   **Strategy**: Use **Amazon Titan Text Lite**.

### 4. Network (API Gateway)
*   **Free Tier**: 1 million calls per month for first 12 months.
*   **Strategy**: Use **HTTP APIs**.

## Development Plan

1.  **Setup**: Initialize Serverless Framework project with Python template.
2.  **Infrastructure**: Define Lambda function, Layer, and HTTP API in `serverless.yml`.
3.  **Backend Logic**:
    *   Implement "Real Quote" logic (MySQL query via `pymysql`).
    *   Implement "AI Quote" logic (Bedrock integration via `boto3`).
4.  **Deployment**: Deploy using Serverless Framework (`sls deploy`).
5.  **Testing**: Verify API endpoints.

## Cost Estimate Scenario: 10 Requests / Day
**Total Monthly Requests**: 300

| Service | Usage | Estimated Cost (Monthly) | Notes |
| :--- | :--- | :--- | :--- |
| **API Gateway** | 300 requests | **$0.00** | Covered by Free Tier (1M req/mo) |
| **Lambda** | 300 invocations (2s duration, 128MB) | **$0.00** | Covered by Free Tier (400k GB-s/mo) |
| **MySQL** | 300 Queries | **$0.00** | Assuming existing infrastructure |
| **Bedrock (Titan Text Lite)** | 15k input / 15k output tokens | **~$0.005** | ~$0.00015/1k in, ~$0.0002/1k out |
| **Total** | | **~$0.005 / month** | < 1 cent per month |
