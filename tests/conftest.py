import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_fake_env_vars():
    os.environ["PINECONE_API_KEY"] = "fake_key"
    os.environ["PINECONE_INDEX_NAME"] = "fake_index"
    yield
