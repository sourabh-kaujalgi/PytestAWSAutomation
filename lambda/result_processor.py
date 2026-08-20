import json
import os
import boto3
import xml.etree.ElementTree as ET
from urllib.parse import unquote_plus


s3 = boto3.client("s3")
sns = boto3.client("sns")

SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]


def lambda_handler(event, context):

    print("Received S3 event:")
    print(json.dumps(event))

    for record in event.get("Records", []):

        bucket = record["s3"]["bucket"]["name"]

        key = unquote_plus(
            record["s3"]["object"]["key"]
        )

        print(f"Processing: s3://{bucket}/{key}")

        # Process only JUnit reports
        if not key.endswith("junit.xml"):
            print(f"Skipping: {key}")
            continue

        response = s3.get_object(
            Bucket=bucket,
            Key=key
        )

        xml_content = response["Body"].read()

        root = ET.fromstring(xml_content)

        total = int(root.attrib.get("tests", 0))
        failures = int(root.attrib.get("failures", 0))
        errors = int(root.attrib.get("errors", 0))
        skipped = int(root.attrib.get("skipped", 0))

        passed = total - failures - errors - skipped

        status = "PASSED"

        if failures > 0 or errors > 0:
            status = "FAILED"

        message = f"""
SauceDemo Pytest Automation Result

Status: {status}

Total Tests : {total}
Passed      : {passed}
Failed      : {failures}
Errors      : {errors}
Skipped     : {skipped}

S3 Report:
s3://{bucket}/{key}
"""

        print(message)

        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"Pytest Automation - {status}",
            Message=message
        )

        print("SNS notification sent successfully")

    return {
        "statusCode": 200,
        "body": json.dumps(
            "Result processing completed"
        )
    }