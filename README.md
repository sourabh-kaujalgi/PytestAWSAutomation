# SauceDemo Pytest + AWS + GitHub Actions Framework

This is a complete starter SDET framework for https://www.saucedemo.com/.

## Test stack

- Python
- Pytest
- Playwright
- Page-independent functional tests
- HTML/JUnit reports
- GitHub Actions

## AWS integrations

### S3
Stores:
- HTML report
- JUnit XML
- screenshots
- logs

Path:

s3://BUCKET/pytest/GITHUB_RUN_ID/

### CloudWatch Logs

Framework can publish a JSON run summary to:

/qa/pytest

### CloudWatch Metrics

Namespace:

QA/Pytest

Metrics:
- TestsPassed
- TestsFailed
- TestsSkipped
- TestDurationSeconds

### CloudWatch Alarm

Alarm triggers when:

TestsFailed >= 1

The alarm publishes to SNS.

### SNS

SNS email subscription is created by Terraform.

The recipient must confirm the SNS subscription email before receiving notifications.

### Lambda

Lambda is included as a result-processing component.

It can:
1. Receive SNS events.
2. Read a result JSON from S3.
3. Aggregate passed/failed/skipped results.
4. Produce a summarized result.
5. Be extended to trigger downstream AWS actions.

## AWS setup

Create/configure the AWS resources from the AWS Console:

1. Create an S3 bucket for test artifacts.
2. Create a CloudWatch Log Group named `/qa/pytest`.
3. Create an SNS topic and an email subscription.
4. Confirm the SNS subscription email.
5. Create a CloudWatch alarm for the `QA/Pytest` / `TestsFailed` metric.
6. Create/deploy the Lambda in `lambda/result_processor.py`.
7. Create a GitHub OIDC IAM role and configure its ARN as the `AWS_ROLE_ARN` GitHub repository variable.

No Terraform is included in this project.

## GitHub Variables

Create repository variables:

AWS_REGION
S3_BUCKET
CLOUDWATCH_LOG_GROUP
CLOUDWATCH_NAMESPACE
SNS_TOPIC_ARN
AWS_ROLE_ARN

AWS_ROLE_ARN must be a GitHub OIDC IAM role.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium

pytest
```

## Important

The AWS IAM role used by GitHub Actions needs permissions for:
- s3:PutObject
- s3:ListBucket
- cloudwatch:PutMetricData
- logs:CreateLogGroup
- logs:CreateLogStream
- logs:PutLogEvents
- sns:Publish

Use least privilege in production.
