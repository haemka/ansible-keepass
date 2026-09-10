import os

import pytest

import secret_reader
import secret_writer


def test_reads_written_entry(db, kdbx_path, reopen_db):
    secret_writer.secret_write(
        secret_path="group1/mysecret", db=db, db_path=kdbx_path,
        username="john", password="doe", url="https://example.com",
        custom_properties={"gender": "Male"},
    )
    db2 = reopen_db()
    secret = secret_reader.secret_to_dic(db2, "group1/mysecret")
    assert secret["mysecret"]["username"] == "john"
    assert secret["mysecret"]["password"] == "doe"
    assert secret["mysecret"]["url"] == "https://example.com"
    assert secret["mysecret"]["gender"] == "Male"


def test_returns_empty_dict_for_missing_secret(db):
    assert secret_reader.secret_to_dic(db, "does/not/exist") == {}


def test_missing_secret_path_raises(db):
    with pytest.raises(ValueError):
        secret_reader.secret_to_dic(db, "")


def test_extract_attachments_to_writes_file(db, kdbx_path, reopen_db, sample_file, tmp_path):
    attachment_path = sample_file("id_rsa", b"secret-key-bytes")
    secret_writer.secret_write(
        secret_path="mysecret", db=db, db_path=kdbx_path,
        attachments=[{"path": attachment_path, "filename": "id_rsa"}],
    )
    db2 = reopen_db()
    out_dir = str(tmp_path / "extracted")
    secret = secret_reader.secret_to_dic(db2, "mysecret", extract_attachments_to=out_dir)
    assert secret["mysecret"]["attachments"] == ["id_rsa"]
    extracted = os.path.join(out_dir, "id_rsa")
    assert os.path.isfile(extracted)
    assert open(extracted, "rb").read() == b"secret-key-bytes"


def test_no_extraction_without_extract_attachments_to(db, kdbx_path, reopen_db, sample_file, tmp_path):
    attachment_path = sample_file("id_rsa")
    secret_writer.secret_write(
        secret_path="mysecret", db=db, db_path=kdbx_path,
        attachments=[{"path": attachment_path, "filename": "id_rsa"}],
    )
    db2 = reopen_db()
    would_be_dir = tmp_path / "should-not-exist"
    secret_reader.secret_to_dic(db2, "mysecret")
    assert not would_be_dir.exists()


def test_attachment_filenames_filters_extraction(db, kdbx_path, reopen_db, sample_file, tmp_path):
    a = sample_file("a.txt", b"aaa")
    b = sample_file("b.txt", b"bbb")
    secret_writer.secret_write(
        secret_path="mysecret", db=db, db_path=kdbx_path,
        attachments=[{"path": a}, {"path": b}],
    )
    db2 = reopen_db()
    out_dir = str(tmp_path / "extracted")
    secret = secret_reader.secret_to_dic(
        db2, "mysecret", extract_attachments_to=out_dir, attachment_filenames=["a.txt"],
    )
    assert sorted(secret["mysecret"]["attachments"]) == ["a.txt", "b.txt"]
    assert sorted(os.listdir(out_dir)) == ["a.txt"]
