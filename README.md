# aiQuotes API Service

This project provides a public API service for generating and retrieving quotes using both a curated database and AI generation (Amazon Bedrock).

## Features

- **Real Quotes**: Retrieve quotes from a curated MySQL database.
- **AI Quotes**: Generate unique quotes on-demand using Amazon Bedrock (Nova Micro).
- **Public Access**: Accessible via a public Lambda Function URL.
- **CORS Support**: Ready for integration into web applications.

## API Usage

The API accepts `POST` requests with a JSON body.

### Base URL
(Get the URL by running `python deploy.py`)
Example: `https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/`

### Endpoints

#### 1. Get a Real Quote (Default)
Retrieves a quote from the internal database.

**Request:**
```json
POST /
Content-Type: application/json

{
  "type": "real",
  "genre": "motivation"
}
```

**Response:**
```json
{
  "quote": "Success is not final...",
  "author": "Winston Churchill",
  "source": "database"
}
```

#### 2. Generate an AI Quote
Generates a new quote using AI based on the genre and optional prompt context.

**Request:**
```json
POST /
Content-Type: application/json

{
  "type": "ai",
  "genre": "life",
  "prompt": "humorous style"
}
```

**Response:**
```json
{
  "quote": "Life is what happens when you're busy making other plans.",
  "author": "AI (Amazon Nova Micro)",
  "source": "bedrock"
}
```

#### 3. List Available AI Models
Lists the Foundation Models available in Bedrock (useful for debugging or future expansion).

**Request:**
```json
POST /
Content-Type: application/json

{
  "type": "list_models"
}
```

## Integration

You can easily call this API from any frontend using `fetch`:

```javascript
const response = await fetch('YOUR_FUNCTION_URL', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    type: 'ai',
    genre: 'technology'
  })
});

const data = await response.json();
console.log(data.quote);
```

## Deployment

To deploy updates to the service:

```bash
python deploy.py
```
