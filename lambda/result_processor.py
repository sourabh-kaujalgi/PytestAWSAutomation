import json
import os
import urllib.parse

import boto3

s3 = boto3.client("s3")


def lambda_handler(event, context):
    """
    Receives an SNS notification and can process a JSON test summary.

    Expected SNS message:
    {
      "bucket": "bucket-name",
      "key": "pytest/123/result.json",
      "passed": 20,
      "failed": 2,
      "skipped": 1
    }
    """

    results = []

    for record in event.get("Records", []):
        message = record.get("Sns", {}).get("Message", "{}")

        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            data = {"message": message}

        bucket = data.get("bucket")
        key = data.get("key")

        if bucket and key:
            obj = s3.get_object(Bucket=bucket, Key=key)
            data = json.loads(obj["Body"].read())

        results.append(data)

    failed = sum(int(x.get("failed", 0)) for x in results)
    passed = sum(int(x.get("passed", 0)) for x in results)
    skipped = sum(int(x.get("skipped", 0)) for x in results)

    summary = {
        "status": "FAILED" if failed else "PASSED",
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "runs": len(results)
    }

    print(json.dumps(summary))
    return summary
