# Banking Analytics - Multi-Agent Collaboration

## Overview

This project is an adaptation of the original [AWS Bedrock Multi-Agents Collaboration Workshop](https://github.com/aws-samples/bedrock-multi-agents-collaboration-workshop), refocused on banking analytics applications.

It showcases how the Amazon Bedrock Agents feature - [multi-agent collaboration capabilities](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-multi-agent-collaboration.html) - can be applied in the banking domain to provide enhanced data analysis and insights.

The system consists of a supervisor agent that orchestrates three specialized sub-agents, each handling specific aspects of banking data analysis, visualization explanation, and risk assessment.

## System Architecture

```
├── 1- Data Analytics Agent
├── 2- Customer Insights Agent
├── 3- Risk & Compliance Agent
├── 4- Banking Insights Supervisor Agent
└── 5- Clean up
```

## Agents Description

### Banking Insights Supervisor Agent

The supervisor agent coordinates the activities of three specialized sub-agents,
routing user queries to the appropriate agent while maintaining context and
ensuring seamless interactions. It provides comprehensive insights by combining information from multiple agents and data sources.

### Sub-Agents

#### 1. Data Analytics Agent

- Translates natural language questions into structured data queries
- Analyzes transaction patterns and customer behaviors
- Provides trend analysis on key banking metrics
- Generates forecasts for account growth, transaction volumes, etc.
- Contains code interpretation capabilities to analyze banking data

#### 2. Customer Insights Agent

- Explains data visualizations in natural language
- Analyzes customer segmentation and profiles
- Tracks customer lifecycle events (acquisition, engagement, churn)
- Identifies at-risk customers for potential churn
- Recommends customer retention strategies

#### 3. Risk & Compliance Agent

- Detects potential fraud patterns in transaction data
- Monitors regulatory compliance metrics
- Identifies unusual account activities
- Assesses credit risk patterns
- Generates compliance reports and alerts

## Workshop Contents

1. Data Analytics agent setup
2. Customer Insights agent setup
3. Risk & Compliance agent setup
4. Multi-agent collaboration setup
5. Supervisor agent invocation
6. Clean up

## Prerequisites

- AWS Account with appropriate permissions
- Amazon Bedrock access
- Basic understanding of AWS services
- Python 3.8+
- Latest Boto3 SDK
- AWS CLI configured

## Getting Started

1. Clone this repository:

```bash
git clone https://github.com/tsynode/multi-agent-collaboration-finance.git
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Follow the setup instructions in the workshop guide, linked in the Overview section.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the MIT-0 License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the repository.

---

Note: This project demonstrates how Amazon Bedrock Agents' multi-agent collaboration feature can be applied in the banking domain with two key capabilities:

1. **Natural Language to Query Translation**: Allowing users to ask questions about banking data in natural language
2. **Visualization Explanation**: Providing natural language explanations of data visualizations

This is an adaptation of the original [AWS Bedrock Multi-Agents Collaboration Workshop](https://github.com/aws-samples/bedrock-multi-agents-collaboration-workshop).
