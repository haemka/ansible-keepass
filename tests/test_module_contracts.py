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


def test_secret_writer_reports_clean_error_on_wrong_password(kdbx_path, db_password):
    run_module("secret_writer", {"db_path": kdbx_path, "db_password": db_password, "secret_path": "mysecret"})
    out = run_module("secret_writer", {
        "db_path": kdbx_path, "db_password": "wrong-password", "secret_path": "othersecret",
    })
    assert out["failed"] is True
    assert "msg" in out


def test_secret_reader_reads_written_entry_end_to_end(kdbx_path, db_password, sample_file, tmp_path):
    attachment_path = sample_file("id_rsa", b"secret-key-bytes")
    run_module("secret_writer", {
        "db_path": kdbx_path, "db_password": db_password, "secret_path": "mysecret",
        "secret_value": {
            "username": "john", "url": "https://example.com",
            "attachments": [{"path": attachment_path, "filename": "id_rsa"}],
        },
    })
    out_dir = str(tmp_path / "extracted")
    out = run_module("secret_reader", {
        "db_path": kdbx_path, "db_password": db_password, "secret_path": "mysecret",
        "extract_attachments_to": out_dir,
    })
    assert out["failed"] is False
    assert out["secret"]["mysecret"]["username"] == "john"
    assert out["secret"]["mysecret"]["url"] == "https://example.com"
    assert out["secret"]["mysecret"]["attachments"] == ["id_rsa"]
    assert out["attachments_extracted_to"] == out_dir
    assert os.path.isfile(os.path.join(out_dir, "id_rsa"))


def test_secret_reader_check_mode_is_a_noop(kdbx_path, db_password, tmp_path):
    run_module("secret_writer", {"db_path": kdbx_path, "db_password": db_password, "secret_path": "mysecret"})
    out_dir = tmp_path / "should-not-be-created"
    out = run_module("secret_reader", {
        "db_path": kdbx_path, "db_password": db_password, "secret_path": "mysecret",
        "extract_attachments_to": str(out_dir),
        "_ansible_check_mode": True,
    })
    assert out["changed"] is True  # secret_reader's default result carries changed=True
    assert not out_dir.exists()


def test_group_reader_reads_written_entries_end_to_end(kdbx_path, db_password, sample_file, tmp_path):
    attachment_path = sample_file("id_rsa", b"secret-key-bytes")
    run_module("secret_writer", {
        "db_path": kdbx_path, "db_password": db_password, "secret_path": "grp/one",
        "secret_value": {
            "username": "john", "url": "https://example.com",
            "attachments": [{"path": attachment_path, "filename": "id_rsa"}],
        },
    })
    out_dir = str(tmp_path / "extracted")
    out = run_module("group_reader", {
        "db_path": kdbx_path, "db_password": db_password, "group_path": "grp",
        "extract_attachments_to": out_dir,
    })
    assert out["failed"] is False
    assert out["group"][0]["one"]["username"] == "john"
    assert out["group"][0]["one"]["url"] == "https://example.com"
    assert out["group"][0]["one"]["attachments"] == ["id_rsa"]
    assert out["attachments_extracted_to"] == out_dir
    assert os.path.isfile(os.path.join(out_dir, "one", "id_rsa"))


def test_group_reader_check_mode_is_a_noop(kdbx_path, db_password, tmp_path):
    run_module("secret_writer", {"db_path": kdbx_path, "db_password": db_password, "secret_path": "grp/one"})
    out_dir = tmp_path / "should-not-be-created"
    out = run_module("group_reader", {
        "db_path": kdbx_path, "db_password": db_password, "group_path": "grp",
        "extract_attachments_to": str(out_dir),
        "_ansible_check_mode": True,
    })
    assert out["changed"] is True  # group_reader's default result carries changed=True
    assert not out_dir.exists()


def test_secret_reader_reports_clean_error_on_wrong_password(kdbx_path, db_password):
    run_module("secret_writer", {"db_path": kdbx_path, "db_password": db_password, "secret_path": "mysecret"})
    out = run_module("secret_reader", {
        "db_path": kdbx_path, "db_password": "wrong-password", "secret_path": "mysecret",
    })
    assert out["failed"] is True
    assert "msg" in out


def test_group_reader_reports_clean_error_on_wrong_password(kdbx_path, db_password):
    run_module("secret_writer", {"db_path": kdbx_path, "db_password": db_password, "secret_path": "grp/mysecret"})
    out = run_module("group_reader", {
        "db_path": kdbx_path, "db_password": "wrong-password", "group_path": "grp",
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
