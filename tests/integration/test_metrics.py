"""Integration tests for metrics exposed by the service."""

import os
import re
from unittest.mock import patch

import pytest
import requests
from fastapi.testclient import TestClient

from ols import config

client: TestClient


# we need to patch the config file path to point to the test
# config file before we import anything from main.py
@pytest.fixture(scope="function", autouse=True)
@patch.dict(
    os.environ, {"RCS_CONFIG_FILE": "tests/config/config_for_integration_tests.yaml"}
)
def _setup():
    """Setups the test client."""
    global client
    config.reload_from_yaml_file("tests/config/config_for_integration_tests.yaml")
    from ols.app.main import app

    client = TestClient(app)


def retrieve_metrics(client):
    """Retrieve all service metrics."""
    response = client.get("/metrics")

    # check that the /metrics endpoint is correct and we got
    # some response
    assert response.status_code == requests.codes.ok
    assert response.text is not None

    # return response text (it is not JSON!)
    return response.text


def test_metrics():
    """Check if service provides metrics endpoint with some expected counters."""
    response_text = retrieve_metrics(client)

    # counters that are expected to be part of metrics
    expected_counters = (
        "ols_rest_api_calls_total",
        "ols_llm_calls_total",
        "ols_llm_calls_failures_total",
        "ols_llm_validation_errors_total",
        "ols_llm_token_sent_total",
        "ols_llm_token_received_total",
        "ols_provider_model_configuration",
    )

    # check if all counters are present
    for expected_counter in expected_counters:
        assert (
            f"{expected_counter} " in response_text
        ), f"Counter {expected_counter} not found in {response_text}"


def get_counter_value(client, counter_name, path, status_code):
    """Retrieve counter value from metrics."""
    # counters with labels have the following format:
    # rest_api_calls_total{path="/openapi.json",status_code="200"} 1.0
    prefix = f'{counter_name}{{path="{path}",status_code="{status_code}"}} '

    response_text = retrieve_metrics(client)
    lines = [line.strip() for line in response_text.split("\n")]

    # try to find the given counter
    for line in lines:
        if line.startswith(prefix):
            without_prefix = line[len(prefix) :]
            # parse as float, convert that float to integer
            return int(float(without_prefix))
    raise Exception(f"Counter {counter_name} was not found in metrics")


def test_rest_api_call_counter_ok_status():
    """Check if REST API call counter works as expected, label with 200 OK status."""
    endpoint = "/readiness"

    # initialize counter with label by calling endpoint
    client.get(endpoint)
    old = get_counter_value(client, "ols_rest_api_calls_total", endpoint, "200")

    # call some REST API endpoint
    client.get(endpoint)
    new = get_counter_value(client, "ols_rest_api_calls_total", endpoint, "200")

    # compare counters
    assert new == old + 1, "Counter has not been updated properly"


def test_rest_api_call_counter_not_found_status():
    """Check if REST API call counter works as expected, label with 404 NotFound status."""
    endpoint = "/this-does-not-exists"

    # initialize counter with label
    client.get(endpoint)
    old = get_counter_value(client, "ols_rest_api_calls_total", endpoint, "404")

    # call some REST API endpoint
    client.get(endpoint)
    new = get_counter_value(client, "ols_rest_api_calls_total", endpoint, "404")

    # compare counters
    # just the NotFound value should change
    assert new == old + 1, "Counter for 404 NotFound  has not been updated properly"


def test_metrics_duration():
    """Check if service provides metrics for durations."""
    response_text = retrieve_metrics(client)

    # duration histograms are expected to be part of metrics

    # first: check summary and statistic
    assert 'response_duration_seconds_count{path="/metrics"}' in response_text
    assert 'response_duration_seconds_sum{path="/metrics"}' in response_text

    # second: check the histogram itself
    pattern = re.compile(
        r"response_duration_seconds_bucket{le=\"0\.[0-9]+\",path=\"\/metrics\"}"
    )
    # re.findall() returns empty list if not found, and this empty list is treated as False
    assert re.findall(pattern, response_text)
    pattern = re.compile(
        r"response_duration_seconds_bucket{le=\"\+Inf\",path=\"\/metrics\"}"
    )
    assert re.findall(pattern, response_text)


def test_provider_model_configuration_metrics():
    """Check if provider_model_configuration metrics shows the expected information."""
    response_text = retrieve_metrics(client)
    print(response_text)
    for provider in ("bam", "openai"):
        for model in ("m1", "m2"):
            if provider == "bam" and model == "m1":
                # default/enabled model should have a metric value of 1.0
                assert (
                    f'provider_model_configuration{{model="{model}",provider="{provider}"}} 1.0'
                    in response_text
                )
            else:
                # non-enabled models should have a metric value of 0.0
                assert (
                    f'provider_model_configuration{{model="{model}",provider="{provider}"}} 0.0'
                    in response_text
                )
