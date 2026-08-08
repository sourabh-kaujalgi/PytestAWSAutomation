import os
import time
from pathlib import Path

import pytest
from framework.aws_services import AWSQAReporter


@pytest.fixture(scope="session")
def browser_type_launch_args():
    return {"headless": True}


@pytest.fixture
def screenshot_on_failure(page, request):
    yield
    if request.node.rep_call.failed:
        Path("screenshots").mkdir(exist_ok=True)
        filename = request.node.nodeid.replace("/", "_").replace("::", "_")
        page.screenshot(path=f"screenshots/{filename}.png", full_page=True)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


def pytest_sessionfinish(session, exitstatus):
    reporter = AWSQAReporter()

    duration = time.time() - getattr(session, "_start_time", time.time())

    stats = session.stats
    passed = len(stats.get("passed", []))
    failed = len(stats.get("failed", []))
    skipped = len(stats.get("skipped", []))

    try:
        reporter.publish_summary(passed, failed, skipped, duration)
        reporter.upload_artifacts()
    except Exception as exc:
        print(f"AWS reporting failed: {exc}")


def pytest_sessionstart(session):
    session._start_time = time.time()
