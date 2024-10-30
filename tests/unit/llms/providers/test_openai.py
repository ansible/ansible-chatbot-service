"""Unit tests for OpenAI provider."""

import httpx
import pytest
from langchain_openai.chat_models.base import ChatOpenAI

from ols.app.models.config import ProviderConfig
from ols.src.llms.providers.openai import OpenAI


@pytest.fixture
def provider_config():
    """Fixture with provider configuration for OpenAI."""
    return ProviderConfig(
        {
            "name": "some_provider",
            "type": "openai",
            "url": "test_url",
            "credentials_path": "tests/config/secret/apitoken",
            "models": [
                {
                    "name": "test_model_name",
                    "url": "http://test_model_url/",
                    "credentials_path": "tests/config/secret/apitoken",
                }
            ],
        }
    )


@pytest.fixture
def provider_config_credentials_directory():
    """Fixture with provider configuration for OpenAI."""
    return ProviderConfig(
        {
            "name": "some_provider",
            "type": "openai",
            "url": "test_url",
            "credentials_path": "tests/config/secret",
            "models": [
                {
                    "name": "test_model_name",
                    "url": "http://test_model_url/",
                    "credentials_path": "tests/config/secret/apitoken",
                }
            ],
        }
    )


@pytest.fixture
def provider_config_with_specific_parameters():
    """Fixture with provider configuration for OpenAI with specific parameters."""
    return ProviderConfig(
        {
            "name": "some_provider",
            "type": "openai",
            "url": "test_url",
            "credentials_path": "tests/config/secret/apitoken",
            "openai_config": {
                "url": "http://openai.com",
                "credentials_path": "tests/config/secret2/apitoken",
            },
            "models": [
                {
                    "name": "test_model_name",
                    "url": "http://test_model_url/",
                    "credentials_path": "tests/config/secret/apitoken",
                }
            ],
        }
    )


def test_basic_interface(provider_config):
    """Test basic interface."""
    openai = OpenAI(model="uber-model", params={}, provider_config=provider_config)
    llm = openai.load()
    assert isinstance(llm, ChatOpenAI)
    assert openai.default_params
    assert "base_url" in openai.default_params
    assert "model" in openai.default_params
    assert "max_tokens" in openai.default_params

    # check the HTTP client parameter
    assert "http_client" in openai.default_params
    assert openai.default_params["http_client"] is not None

    client = openai.default_params["http_client"]
    assert isinstance(client, httpx.Client)


def test_params_handling(provider_config):
    """Test that not allowed parameters are removed before model init."""
    # first three parameters should be removed before model init
    # rest need to stay
    params = {
        "unknown_parameter": "foo",
        "min_new_tokens": 1,
        "max_new_tokens": 10,
        "temperature": 0.3,
        "verbose": True,
    }

    openai = OpenAI(model="uber-model", params=params, provider_config=provider_config)
    llm = openai.load()
    assert isinstance(llm, ChatOpenAI)
    assert openai.default_params
    assert openai.params

    # known parameters should be there
    assert "temperature" in openai.params
    assert "verbose" in openai.params
    assert openai.params["temperature"] == 0.3
    assert openai.params["verbose"] is True

    # unknown parameters should be filtered out
    assert "min_new_tokens" not in openai.params
    assert "max_new_tokens" not in openai.params
    assert "unknown_parameter" not in openai.params

    # taken from configuration
    assert openai.url == "test_url"
    assert openai.credentials == "secret_key"

    # API key should be loaded from secret
    assert openai.default_params["openai_api_key"] == "secret_key"

    assert openai.default_params["base_url"] == "test_url"


def test_credentials_key_in_directory_handling(provider_config_credentials_directory):
    """Test that credentials in directory is handled as expected."""
    params = {}

    openai = OpenAI(
        model="uber-model",
        params=params,
        provider_config=provider_config_credentials_directory,
    )
    llm = openai.load()
    assert isinstance(llm, ChatOpenAI)

    assert openai.credentials == "secret_key"


def test_loading_provider_specific_parameters(provider_config_with_specific_parameters):
    """Test that not allowed parameters are removed before model init."""
    openai = OpenAI(
        model="uber-model",
        params={},
        provider_config=provider_config_with_specific_parameters,
    )
    llm = openai.load()
    assert isinstance(llm, ChatOpenAI)
    assert openai.default_params
    assert openai.params

    assert "base_url" in openai.default_params
    assert "model" in openai.default_params
    assert "max_tokens" in openai.default_params

    # parameters taken from provier-specific configuration
    # which takes precedence over regular configuration
    assert openai.url == "http://openai.com/"
    assert openai.credentials == "secret_key_2"

    assert openai.default_params["openai_api_key"] == "secret_key_2"
    assert openai.default_params["base_url"] == "http://openai.com/"


def test_none_params_handling(provider_config):
    """Test that not allowed parameters are removed before model init."""
    # first three parameters should be removed before model init
    # rest need to stay
    params = {
        "unknown_parameter": None,
        "min_new_tokens": None,
        "max_new_tokens": None,
        "organization": None,
        "cache": None,
    }

    openai = OpenAI(model="uber-model", params=params, provider_config=provider_config)
    llm = openai.load()
    assert isinstance(llm, ChatOpenAI)
    assert openai.default_params
    assert openai.params

    # API key should be loaded from secret provided in specific param
    assert openai.default_params["openai_api_key"] == "secret_key"

    # base_url too should be read from specific params
    assert openai.default_params["base_url"] == "test_url"


def test_params_replace_default_values_with_none(provider_config):
    """Test if default values are replaced by None values."""
    # provider initialization with empty set of params
    openai = OpenAI(model="uber-model", params={}, provider_config=provider_config)
    openai.load()

    # check default value
    assert "base_url" in openai.params
    assert openai.params["base_url"] is not None

    # try to override default parameter
    params = {"base_url": None}

    openai = OpenAI(model="uber-model", params=params, provider_config=provider_config)
    openai.load()

    # known parameter(s) should be there, now with None values
    assert "base_url" in openai.params
    assert openai.params["base_url"] is None
