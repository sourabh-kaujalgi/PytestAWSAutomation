import json
import logging
import os
import time
from pathlib import Path

import boto3


class AWSQAReporter:
    """Uploads test artifacts and publishes CloudWatch/SNS data."""

    def __init__(self):
        self.region = os.getenv("AWS_REGION", "ap-south-1")
        self.bucket = os.getenv("S3_BUCKET")
        self.log_group = os.getenv("CLOUDWATCH_LOG_GROUP", "/qa/pytest")
        self.namespace = os.getenv("CLOUDWATCH_NAMESPACE", "QA/Pytest")
        self.sns_topic_arn = os.getenv("SNS_TOPIC_ARN")
        self.run_id = os.getenv("GITHUB_RUN_ID", f"local-{int(time.time())}")

        self.s3 = boto3.client("s3", region_name=self.region)
        self.logs = boto3.client("logs", region_name=self.region)
        self.cloudwatch = boto3.client("cloudwatch", region_name=self.region)
        self.sns = boto3.client("sns", region_name=self.region)

    def upload_directory(self, directory):
        if not self.bucket:
            logging.warning("S3_BUCKET is not configured; skipping S3 upload.")
            return

        directory = Path(directory)
        if not directory.exists():
            return

        for file in directory.rglob("*"):
            if file.is_file():
                key = f"pytest/{self.run_id}/{directory.name}/{file.name}"
                logging.info("Uploading %s -> s3://%s/%s", file, self.bucket, key)
                self.s3.upload_file(str(file), self.bucket, key)

    def upload_artifacts(self):
        for directory in ["reports", "screenshots", "logs"]:
            self.upload_directory(directory)

    def ensure_log_stream(self):
        try:
            self.logs.create_log_group(logGroupName=self.log_group)
        except self.logs.exceptions.ResourceAlreadyExistsException:
            pass

        stream = f"run-{self.run_id}"
        try:
            self.logs.create_log_stream(
                logGroupName=self.log_group,
                logStreamName=stream
            )
        except self.logs.exceptions.ResourceAlreadyExistsException:
            pass

        return stream

    def put_log(self, message):
        stream = self.ensure_log_stream()

        self.logs.put_log_events(
            logGroupName=self.log_group,
            logStreamName=stream,
            logEvents=[{
                "timestamp": int(time.time() * 1000),
                "message": message
            }]
        )

    def publish_metrics(self, passed, failed, skipped, duration):
        self.cloudwatch.put_metric_data(
            Namespace=self.namespace,
            MetricData=[
                {
                    "MetricName": "TestsPassed",
                    "Value": passed,
                    "Unit": "Count"
                },
                {
                    "MetricName": "TestsFailed",
                    "Value": failed,
                    "Unit": "Count"
                },
                {
                    "MetricName": "TestsSkipped",
                    "Value": skipped,
                    "Unit": "Count"
                },
                {
                    "MetricName": "TestDurationSeconds",
                    "Value": duration,
                    "Unit": "Seconds"
                }
            ]
        )

    def notify_sns(self, subject, message):
        if not self.sns_topic_arn:
            logging.warning("SNS_TOPIC_ARN is not configured.")
            return

        self.sns.publish(
            TopicArn=self.sns_topic_arn,
            Subject=subject[:100],
            Message=message
        )

    def publish_summary(self, passed, failed, skipped, duration):
        summary = {
            "run_id": self.run_id,
            "repository": os.getenv("GITHUB_REPOSITORY", "local"),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "duration_seconds": round(duration, 2),
            "status": "FAILED" if failed else "PASSED"
        }

        self.put_log(json.dumps(summary))
        self.publish_metrics(passed, failed, skipped, duration)

        if failed:
            self.notify_sns(
                "SauceDemo Pytest Failure",
                json.dumps(summary, indent=2)
            )
