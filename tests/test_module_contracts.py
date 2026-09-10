import os

from helpers import run_module


def test_secret_writer_creates_entry_and_creates_db(kdbx_path, db_password):
    assert not os.path.exists(kdbx_path)
    out = run_module("secret_writer", {
        "db_path": kdbx_path, "db_password": db_password, "secret_path": "mysecret",
        "secret_value": {"username": "john"},
    })
    assert out["failed"] is False
    assert out["changed"] is True
    assert out["secret"]["mysecret"]["username"] == "john"
    assert os.path.isfile(kdbx_path)


def test_secret_writer_check_mode_is_a_noop(kdbx_path, db_password):
    out = run_module("secret_writer", {
        "db_path": kdbx_path, "db_password": db_password, "secret_path": "mysecret",
        "_ansible_check_mode": True,
    })
    assert out["changed"] is False
    assert not os.path.exists(kdbx_path)


def test_secret_writer_without_secret_value_does_not_crash(kdbx_path, db_password):
    out = run_module("secret_writer", {"db_path": kdbx_path, "db_password": db_password, "secret_path": "mysecret"})
    assert out["failed"] is False
    assert out["changed"] is True


def test_secret_reader_reports_clean_error_on_wrong_password(kdbx_path, db_password):
    run_module("secret_writer", {"db_path": kdbx_path, "db_password": db_password, "secret_path": "mysecret"})
    out = run_module("secret_reader", {
        "db_path": kdbx_path, "db_password": "wrong-password", "secret_path": "mysecret",
    })
    assert out["failed"] is True
    assert "msg" in out


def test_secret_reader_attachment_filenames_requires_extract_dir(kdbx_path, db_password):
    run_module("secret_writer", {"db_path": kdbx_path, "db_password": db_password, "secret_path": "mysecret"})
    out = run_module("secret_reader", {
        "db_path": kdbx_path, "db_password": db_password, "secret_path": "mysecret",
        "attachment_filenames": ["x"],
    })
    assert out["failed"] is True
    assert "extract_attachments_to" in out["msg"]


def test_group_reader_attachment_filenames_requires_extract_dir(kdbx_path, db_password):
    run_module("secret_writer", {"db_path": kdbx_path, "db_password": db_password, "secret_path": "grp/mysecret"})
    out = run_module("group_reader", {
        "db_path": kdbx_path, "db_password": db_password, "group_path": "grp",
        "attachment_filenames": ["x"],
    })
    assert out["failed"] is True
    assert "extract_attachments_to" in out["msg"]
