import json
import os
import boto3
from datetime import datetime


sns = boto3.client("sns")


def lambda_handler(event, context):

    print("Lambda triggered successfully")
    print("Event:")
    print(json.dumps(event))

    sns_topic_arn = os.environ.get("SNS_TOPIC_ARN")

    for record in event.get("Records", []):

        event_name = record.get("eventName", "")

        if event_name.startswith("ObjectCreated"):

            bucket = record["s3"]["bucket"]["name"]
            key = record["s3"]["object"]["key"]

            print("New S3 object detected:")
            print(f"Bucket: {bucket}")
            print(f"Key: {key}")

            message = (
                f"Pytest report uploaded successfully.\n\n"
                f"Bucket: {bucket}\n"
                f"Object: {key}\n"
                f"Time: {datetime.utcnow().isoformat()}"
            )

            if sns_topic_arn:

                sns.publish(
                    TopicArn=sns_topic_arn,
                    Subject="Pytest Automation Result",
                    Message=message
                )

                print("SNS notification sent successfully.")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Pytest result processed successfully"
        })
    }