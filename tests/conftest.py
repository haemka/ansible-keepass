import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugins", "modules"))

import pytest
from pykeepass import create_database, PyKeePass


@pytest.fixture
def db_password():
    return "password"


@pytest.fixture
def kdbx_path(tmp_path):
    return str(tmp_path / "test.kdbx")


@pytest.fixture
def db(kdbx_path, db_password):
    create_database(kdbx_path, db_password)
    return PyKeePass(filename=kdbx_path, password=db_password)


@pytest.fixture
def reopen_db(kdbx_path, db_password):
    def _reopen():
        return PyKeePass(filename=kdbx_path, password=db_password)
    return _reopen


@pytest.fixture
def sample_file(tmp_path):
    def _make(name, content=b"sample-content"):
        path = tmp_path / name
        path.write_bytes(content)
        return str(path)
    return _make
