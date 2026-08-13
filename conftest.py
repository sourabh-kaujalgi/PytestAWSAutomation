import json
import logging
import os
from pathlib import Path

import boto3
import pytest


# ============================================================
# Configuration
# ============================================================

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

CLOUDWATCH_NAMESPACE = os.getenv(
    "CLOUDWATCH_NAMESPACE",
    "QA/Pytest"
)

REPORTS_DIR = Path("reports")
SCREENSHOTS_DIR = Path("screenshots")

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
# Pytest report hook
# ============================================================

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Make the pytest test report available to fixtures.

    This allows screenshot_on_failure to determine whether
    the actual test call failed.
    """

    outcome = yield

    report = outcome.get_result()

    setattr(item, f"rep_{report.when}", report)

    # Count setup/teardown errors
    if report.when in ("setup", "teardown"):
        if report.failed:
            TEST_RESULTS["errors"] += 1


# ============================================================
# Screenshot on failure fixture
# ============================================================

@pytest.fixture
def screenshot_on_failure(page, request):
    """
    Take a screenshot automatically when a test fails.

    Screenshots are saved under:

        screenshots/<test_name>.png
    """

    yield

    # Only take screenshot if the actual test call failed
    if (
        hasattr(request.node, "rep_call")
        and request.node.rep_call.failed
    ):

        SCREENSHOTS_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        # Create filesystem-safe filename
        test_name = request.node.name

        test_name = (
            test_name
            .replace("/", "_")
            .replace("\\", "_")
            .replace(":", "_")
            .replace("[", "_")
            .replace("]", "_")
        )

        screenshot_path = (
            SCREENSHOTS_DIR / f"{test_name}.png"
        )

        try:
            page.screenshot(
                path=str(screenshot_path),
                full_page=True
            )

            logger.info(
                "Screenshot saved: %s",
                screenshot_path
            )

            print(
                f"\nScreenshot saved: {screenshot_path}"
            )

        except Exception as exc:
            logger.error(
                "Unable to capture screenshot: %s",
                exc
            )


# ============================================================
# Collect individual test results
# ============================================================

def pytest_runtest_logreport(report):
    """
    Collect test results.

    Only the 'call' phase is counted as the actual test result.
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
# Test start logging
# ============================================================

def pytest_runtest_logstart(nodeid, location):
    logger.info(
        "Starting test: %s",
        nodeid
    )


# ============================================================
# Test finish logging
# ============================================================

def pytest_runtest_logfinish(nodeid, location):
    logger.info(
        "Finished test: %s",
        nodeid
    )


# ============================================================
# Create JSON test report
# ============================================================

def create_test_report(exitstatus):
    """
    Create:

        reports/test_results.json
    """

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    overall_status = (
        "PASSED"
        if (
            TEST_RESULTS["failed"] == 0
            and TEST_RESULTS["errors"] == 0
            and exitstatus == 0
        )
        else "FAILED"
    )

    result = {
        "total": TEST_RESULTS["total"],
        "passed": TEST_RESULTS["passed"],
        "failed": TEST_RESULTS["failed"],
        "skipped": TEST_RESULTS["skipped"],
        "errors": TEST_RESULTS["errors"],
        "exit_status": int(exitstatus),
        "status": overall_status
    }

    with open(
        RESULT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            indent=4
        )

    logger.info(
        "Test result report created: %s",
        RESULT_FILE
    )

    print(
        f"\nTest result report created: {RESULT_FILE}"
    )


# ============================================================
# Publish CloudWatch metrics
# ============================================================

def publish_cloudwatch_metrics():
    """
    Publish pytest results to CloudWatch.
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
            },
            {
                "MetricName": "TestErrors",
                "Value": TEST_RESULTS["errors"],
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

        print(
            "CloudWatch metrics published successfully"
        )

    except Exception as exc:

        logger.error(
            "Failed to publish CloudWatch metrics: %s",
            exc
        )

        print(
            f"CloudWatch metric publishing failed: {exc}"
        )


# ============================================================
# Pytest session finish
# ============================================================

def pytest_sessionfinish(session, exitstatus):
    """
    Runs once after the complete pytest session.

    Compatible with pytest 8.x.

    IMPORTANT:
    We do NOT use session.stats because that attribute
    does not exist in pytest 8.x.
    """

    print("\n")
    print("=" * 60)
    print("             TEST EXECUTION SUMMARY")
    print("=" * 60)

    print(
        f"Total Tests : {TEST_RESULTS['total']}"
    )

    print(
        f"Passed      : {TEST_RESULTS['passed']}"
    )

    print(
        f"Failed      : {TEST_RESULTS['failed']}"
    )

    print(
        f"Skipped     : {TEST_RESULTS['skipped']}"
    )

    print(
        f"Errors      : {TEST_RESULTS['errors']}"
    )

    print(
        f"Exit Status : {exitstatus}"
    )

    if (
        TEST_RESULTS["failed"] == 0
        and TEST_RESULTS["errors"] == 0
        and exitstatus == 0
    ):

        print(
            "Overall Status: PASSED"
        )

    else:

        print(
            "Overall Status: FAILED"
        )

    print("=" * 60)

    # Create JSON report
    create_test_report(exitstatus)

    # Publish CloudWatch metrics
    publish_cloudwatch_metrics()