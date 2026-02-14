# aiQuotes - Cost Analysis Report

## Overview
This document provides a comprehensive cost analysis for the aiQuotes serverless API project. The analysis covers different usage scenarios, cost breakdowns, and optimization recommendations for developers who want to fork and deploy this project.

## Current Implementation Summary
- **AWS Region**: us-east-1
- **Lambda Runtime**: Python 3.12 on ARM64 (Graviton)
- **Memory**: 128MB
- **Timeout**: 10 seconds
- **AI Model**: Amazon Nova Micro v1:0
- **Database**: MySQL (external)
- **API Gateway**: HTTP API

## Cost Components Breakdown

### 1. AWS Lambda Costs
**Pricing**: $0.0000166667 per GB-second + $0.20 per 1M requests

**Calculation per request**:
- Memory: 128MB = 0.125GB
- Average execution time: 2 seconds (AI requests), 0.5 seconds (database requests)
- Cost per AI request: 0.125GB × 2s × $0.0000166667 = $0.0000041667
- Cost per DB request: 0.125GB × 0.5s × $0.0000166667 = $0.0000010417

### 2. Amazon Bedrock Costs (Amazon Nova Micro v1:0)
**Pricing**: 
- Input tokens: $0.00015 per 1K tokens
- Output tokens: $0.00060 per 1K tokens

**Average token usage per AI quote**:
- Input tokens: ~150 tokens (prompt + system instructions)
- Output tokens: ~100 tokens (generated quote)
- Cost per AI request: (150/1000 × $0.00015) + (100/1000 × $0.00060) = $0.0000825

### 3. API Gateway HTTP API Costs
**Pricing**: $1.00 per 1M requests + $0.90 per GB data transfer

**Calculation per request**:
- Request cost: $0.000001 per request
- Data transfer: ~2KB per response = negligible

### 4. Database Costs
*Note: Database costs are not included as the project uses an external MySQL database*

## Usage Scenarios and Cost Estimates

### Scenario 1: Personal Use (Low Traffic)
- **Requests per month**: 300 (10 per day)
- **AI vs Database ratio**: 50/50

**Monthly Cost Breakdown**:
| Service | Usage | Cost |
|----------|-------|------|
| Lambda | 150 AI requests + 150 DB requests | $0.00078 |
| Bedrock | 150 AI requests | $0.01238 |
| API Gateway | 300 requests | $0.00030 |
| **Total** | | **$0.01346** |

### Scenario 2: Small Application (Medium Traffic)
- **Requests per month**: 10,000
- **AI vs Database ratio**: 30/70

**Monthly Cost Breakdown**:
| Service | Usage | Cost |
|----------|-------|------|
| Lambda | 3,000 AI + 7,000 DB requests | $0.026 |
| Bedrock | 3,000 AI requests | $0.248 |
| API Gateway | 10,000 requests | $0.01 |
| **Total** | | **$0.284** |

### Scenario 3: Popular Application (High Traffic)
- **Requests per month**: 100,000
- **AI vs Database ratio**: 20/80

**Monthly Cost Breakdown**:
| Service | Usage | Cost |
|----------|-------|------|
| Lambda | 20,000 AI + 80,000 DB requests | $0.26 |
| Bedrock | 20,000 AI requests | $1.65 |
| API Gateway | 100,000 requests | $0.10 |
| **Total** | | **$2.01** |

### Scenario 4: Viral Application (Very High Traffic)
- **Requests per month**: 1,000,000
- **AI vs Database ratio**: 10/90

**Monthly Cost Breakdown**:
| Service | Usage | Cost |
|----------|-------|------|
| Lambda | 100,000 AI + 900,000 DB requests | $2.60 |
| Bedrock | 100,000 AI requests | $8.25 |
| API Gateway | 1,000,000 requests | $1.00 |
| **Total** | | **$11.85** |

## Free Tier Coverage

### AWS Free Tier (First 12 Months)
- **Lambda**: 1M free requests per month + 400,000 GB-seconds
- **API Gateway**: 1M free HTTP API requests per month
- **Bedrock**: No free tier for model inference

**Free Tier Coverage Analysis**:
- For up to 1M requests/month: Only Bedrock costs apply
- Lambda and API Gateway costs are completely covered by free tier
- **Effective cost for 1M requests**: ~$8.25/month (just Bedrock)

## Cost Optimization Recommendations

### 1. Model Selection Strategy
- **Current**: Amazon Nova Micro v1:0 ($0.00015/1K in, $0.00060/1K out)
- **Alternative 1**: Amazon Titan Text Lite ($0.00015/1K in, $0.00020/1K out) - 66% cheaper output
- **Alternative 2**: Claude 3 Haiku ($0.00080/1K in, $0.00400/1K out) - Higher quality but 5-6x more expensive

### 2. Lambda Optimization
- **Memory**: Consider reducing to 128MB (current) or even 64MB if possible
- **Architecture**: ARM64 (Graviton) provides ~20% cost savings over x86
- **Timeout**: Keep at 10 seconds to avoid unnecessary charges

### 3. Caching Strategy
- Implement Redis/Memcached for frequent database queries
- Cache AI responses for common prompts to reduce Bedrock calls
- Use API Gateway caching for static responses

### 4. Monitoring and Budgets
- Set up AWS Budgets with alerts at $1, $5, and $10 thresholds
- Use CloudWatch metrics to monitor usage patterns
- Implement cost allocation tags for better tracking

## Implementation Notes for Developers

### 1. Environment Setup
```bash
# Install Serverless Framework
npm install -g serverless

# Configure AWS credentials
serverless config credentials --provider aws --key ACCESS_KEY --secret SECRET_KEY
```

### 2. Deployment Costs
- **Serverless Framework**: Free to use
- **Deployment time**: ~2-3 minutes per deployment
- **Deployment frequency**: Minimal impact on costs

### 3. Database Considerations
- The project assumes an external MySQL database
- For AWS RDS MySQL: ~$15-30/month for smallest instance
- Consider Amazon Aurora Serverless for variable workloads

### 4. Security and Compliance
- All costs are for us-east-1 region
- Prices may vary by region
- Ensure proper IAM roles to prevent unauthorized usage

## Risk Assessment

### Low Risk Factors
- Predictable pricing model (per request/token)
- Serverless architecture scales to zero when not used
- Free tier covers most initial usage

### Medium Risk Factors
- Bedrock costs can accumulate with high AI usage
- Database costs if using AWS RDS (not included in current setup)
- Potential for API abuse leading to unexpected costs

### High Risk Factors
- **None identified** - Maximum monthly cost for 1M requests is under $12

## Conclusion
The aiQuotes project is extremely cost-effective, with monthly costs ranging from less than 1 cent for personal use to under $12 for 1 million requests. The serverless architecture ensures you only pay for what you use, and the free tier covers most infrastructure costs for the first year.

**Key Takeaways**:
- Bedrock inference is the primary cost driver for AI features
- Lambda and API Gateway costs are minimal and covered by free tier
- Total costs scale linearly with usage
- Maximum risk exposure is very low (<$12/month even at high scale)

For developers forking this project, you can confidently deploy knowing that cost overruns are extremely unlikely and the architecture is optimized for cost efficiency.