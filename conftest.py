import json
import logging
import os
from pathlib import Path

import boto3


# ============================================================
# Configuration
# ============================================================

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
CLOUDWATCH_NAMESPACE = os.getenv(
    "CLOUDWATCH_NAMESPACE",
    "QA/Pytest"
)

REPORTS_DIR = Path("reports")
RESULT_FILE = REPORTS_DIR / "test_results.json"


# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# Test result storage
# ============================================================

TEST_RESULTS = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "errors": 0
}


# ============================================================
# Collect individual test results
# ============================================================

def pytest_runtest_logreport(report):
    """
    Collect test results after the actual test call.

    We only process the 'call' phase so that setup/teardown
    aren't counted as additional tests.
    """

    if report.when != "call":
        return

    TEST_RESULTS["total"] += 1

    if report.passed:
        TEST_RESULTS["passed"] += 1

    elif report.failed:
        TEST_RESULTS["failed"] += 1

    elif report.skipped:
        TEST_RESULTS["skipped"] += 1


# ============================================================
# Handle setup/teardown errors
# ============================================================

def pytest_runtest_logstart(nodeid, location):
    """
    Called when a test starts.
    """
    logger.info("Starting test: %s", nodeid)


def pytest_runtest_logfinish(nodeid, location):
    """
    Called when a test finishes.
    """
    logger.info("Finished test: %s", nodeid)


# ============================================================
# Create JSON test report
# ============================================================

def create_test_report(exitstatus):
    """
    Create reports/test_results.json
    """

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    result = {
        "total": TEST_RESULTS["total"],
        "passed": TEST_RESULTS["passed"],
        "failed": TEST_RESULTS["failed"],
        "skipped": TEST_RESULTS["skipped"],
        "errors": TEST_RESULTS["errors"],
        "exit_status": int(exitstatus),
        "status": (
            "PASSED"
            if TEST_RESULTS["failed"] == 0
            and TEST_RESULTS["errors"] == 0
            and exitstatus == 0
            else "FAILED"
        )
    }

    with open(RESULT_FILE, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=4)

    logger.info(
        "Test result report created: %s",
        RESULT_FILE
    )


# ============================================================
# Publish CloudWatch metrics
# ============================================================

def publish_cloudwatch_metrics():
    """
    Publish pytest results as CloudWatch custom metrics.
    """

    try:
        cloudwatch = boto3.client(
            "cloudwatch",
            region_name=AWS_REGION
        )

        metric_data = [
            {
                "MetricName": "TestTotal",
                "Value": TEST_RESULTS["total"],
                "Unit": "Count"
            },
            {
                "MetricName": "TestPassed",
                "Value": TEST_RESULTS["passed"],
                "Unit": "Count"
            },
            {
                "MetricName": "TestFailed",
                "Value": TEST_RESULTS["failed"],
                "Unit": "Count"
            },
            {
                "MetricName": "TestSkipped",
                "Value": TEST_RESULTS["skipped"],
                "Unit": "Count"
            }
        ]

        cloudwatch.put_metric_data(
            Namespace=CLOUDWATCH_NAMESPACE,
            MetricData=metric_data
        )

        logger.info(
            "CloudWatch metrics published successfully. "
            "Namespace=%s",
            CLOUDWATCH_NAMESPACE
        )

    except Exception as exc:
        # Don't hide the original pytest result if
        # CloudWatch publishing fails.
        logger.error(
            "Failed to publish CloudWatch metrics: %s",
            exc
        )


# ============================================================
# Pytest session finish
# ============================================================

def pytest_sessionfinish(session, exitstatus):
    """
    Runs once after the complete pytest session.

    This replaces the old session.stats implementation,
    which is not available in pytest 8.x.
    """

    print("\n")
    print("=" * 60)
    print("                 TEST EXECUTION SUMMARY")
    print("=" * 60)

    print(f"Total Tests : {TEST_RESULTS['total']}")
    print(f"Passed      : {TEST_RESULTS['passed']}")
    print(f"Failed      : {TEST_RESULTS['failed']}")
    print(f"Skipped     : {TEST_RESULTS['skipped']}")
    print(f"Exit Status : {exitstatus}")

    if TEST_RESULTS["failed"] == 0 and exitstatus == 0:
        print("Overall Status: PASSED")
    else:
        print("Overall Status: FAILED")

    print("=" * 60)

    # Create JSON report
    create_test_report(exitstatus)

    # Publish CloudWatch metrics
    publish_cloudwatch_metrics()