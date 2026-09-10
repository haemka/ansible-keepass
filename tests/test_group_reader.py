import os

import pytest

import group_reader
import secret_writer


def test_reads_all_entries_in_group(db, kdbx_path, reopen_db):
    secret_writer.secret_write(
        secret_path="grp/one", db=db, db_path=kdbx_path,
        username="a", password="pass-a", url="https://example.com",
        custom_properties={"gender": "Male"},
    )
    secret_writer.secret_write(secret_path="grp/two", db=db, db_path=kdbx_path, username="b")
    db2 = reopen_db()
    group = group_reader.group_to_dic(db2, "grp")
    names = {list(entry.keys())[0] for entry in group}
    assert names == {"one", "two"}
    one = next(entry["one"] for entry in group if "one" in entry)
    assert one["password"] == "pass-a"
    assert one["url"] == "https://example.com"
    assert one["gender"] == "Male"


def test_returns_empty_list_for_missing_group(db):
    assert group_reader.group_to_dic(db, "does/not/exist") == []


def test_missing_group_path_raises(db):
    with pytest.raises(ValueError):
        group_reader.group_to_dic(db, "")


def test_extract_attachments_to_nests_per_entry(db, kdbx_path, reopen_db, sample_file, tmp_path):
    attachment_path = sample_file("id_rsa", b"secret-key-bytes")
    secret_writer.secret_write(
        secret_path="grp/one", db=db, db_path=kdbx_path,
        attachments=[{"path": attachment_path, "filename": "id_rsa"}],
    )
    db2 = reopen_db()
    out_dir = str(tmp_path / "extracted")
    group_reader.group_to_dic(db2, "grp", extract_attachments_to=out_dir)
    extracted = os.path.join(out_dir, "one", "id_rsa")
    assert os.path.isfile(extracted)
    assert open(extracted, "rb").read() == b"secret-key-bytes"


def test_attachment_filenames_filters_extraction(db, kdbx_path, reopen_db, sample_file, tmp_path):
    a = sample_file("a.txt", b"aaa")
    b = sample_file("b.txt", b"bbb")
    secret_writer.secret_write(
        secret_path="grp/one", db=db, db_path=kdbx_path,
        attachments=[{"path": a}, {"path": b}],
    )
    db2 = reopen_db()
    out_dir = str(tmp_path / "extracted")
    group_reader.group_to_dic(db2, "grp", extract_attachments_to=out_dir, attachment_filenames=["b.txt"])
    assert sorted(os.listdir(os.path.join(out_dir, "one"))) == ["b.txt"]
