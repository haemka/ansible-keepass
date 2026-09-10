import pytest

import secret_writer


def test_creates_entry_at_root(db, kdbx_path):
    secret, changed = secret_writer.secret_write(
        secret_path="mysecret", db=db, db_path=kdbx_path,
        username="john", password="doe",
    )
    assert changed is True
    assert secret["mysecret"]["username"] == "john"
    assert secret["mysecret"]["password"] == "doe"


def test_creates_entry_in_nested_groups(db, kdbx_path):
    secret, changed = secret_writer.secret_write(
        secret_path="group1/group2/mysecret", db=db, db_path=kdbx_path,
        username="john",
    )
    assert changed is True
    assert secret["mysecret"]["username"] == "john"
    assert db.find_groups(path=["group1", "group2"], first=True) is not None


def test_missing_username_and_password_does_not_crash(db, kdbx_path):
    secret, changed = secret_writer.secret_write(secret_path="empty", db=db, db_path=kdbx_path)
    assert changed is True
    assert "username" not in secret["empty"]
    assert "password" not in secret["empty"]


def test_missing_username_and_password_does_not_crash_nested(db, kdbx_path):
    secret, changed = secret_writer.secret_write(secret_path="grp/empty", db=db, db_path=kdbx_path)
    assert changed is True
    assert "username" not in secret["empty"]


def test_idempotent_without_force(db, kdbx_path, reopen_db):
    secret_writer.secret_write(secret_path="mysecret", db=db, db_path=kdbx_path, username="john")
    db2 = reopen_db()
    secret, changed = secret_writer.secret_write(secret_path="mysecret", db=db2, db_path=kdbx_path, username="jane")
    assert changed is False
    assert secret["mysecret"]["username"] == "john"


def test_force_replaces_entry(db, kdbx_path, reopen_db):
    secret_writer.secret_write(secret_path="mysecret", db=db, db_path=kdbx_path, username="john")
    db2 = reopen_db()
    secret, changed = secret_writer.secret_write(
        secret_path="mysecret", db=db2, db_path=kdbx_path, username="jane", force=True,
    )
    assert changed is True
    assert secret["mysecret"]["username"] == "jane"


def test_force_replaces_entry_with_custom_properties(db, kdbx_path, reopen_db):
    secret_writer.secret_write(secret_path="mysecret", db=db, db_path=kdbx_path, username="john")
    db2 = reopen_db()
    secret, changed = secret_writer.secret_write(
        secret_path="mysecret", db=db2, db_path=kdbx_path, username="jane",
        custom_properties={"gender": "Female"}, force=True,
    )
    assert changed is True
    assert secret["mysecret"]["gender"] == "Female"


def test_idempotent_without_force_nested(db, kdbx_path, reopen_db):
    secret_writer.secret_write(secret_path="grp/mysecret", db=db, db_path=kdbx_path, username="john")
    db2 = reopen_db()
    secret, changed = secret_writer.secret_write(
        secret_path="grp/mysecret", db=db2, db_path=kdbx_path, username="jane",
    )
    assert changed is False
    assert secret["mysecret"]["username"] == "john"


def test_force_replaces_entry_nested(db, kdbx_path, reopen_db):
    secret_writer.secret_write(secret_path="grp/mysecret", db=db, db_path=kdbx_path, username="john")
    db2 = reopen_db()
    secret, changed = secret_writer.secret_write(
        secret_path="grp/mysecret", db=db2, db_path=kdbx_path, username="jane",
        custom_properties={"gender": "Female"}, force=True,
    )
    assert changed is True
    assert secret["mysecret"]["username"] == "jane"
    assert secret["mysecret"]["gender"] == "Female"


def test_url_and_custom_properties_round_trip(db, kdbx_path):
    secret, changed = secret_writer.secret_write(
        secret_path="mysecret", db=db, db_path=kdbx_path,
        url="https://example.com", custom_properties={"gender": "Male"},
    )
    assert secret["mysecret"]["url"] == "https://example.com"
    assert secret["mysecret"]["gender"] == "Male"


def test_attachment_written_with_correct_content(db, kdbx_path, sample_file):
    attachment_path = sample_file("id_rsa", b"secret-key-bytes")
    secret, changed = secret_writer.secret_write(
        secret_path="mysecret", db=db, db_path=kdbx_path,
        attachments=[{"path": attachment_path, "filename": "id_rsa"}],
    )
    assert secret["mysecret"]["attachments"] == ["id_rsa"]
    entry = db.find_entries_by_path(path=["mysecret"])
    assert entry.attachments[0].data == b"secret-key-bytes"


def test_attachment_filename_defaults_to_basename(db, kdbx_path, sample_file):
    attachment_path = sample_file("notes.txt")
    secret, changed = secret_writer.secret_write(
        secret_path="mysecret", db=db, db_path=kdbx_path,
        attachments=[{"path": attachment_path}],
    )
    assert secret["mysecret"]["attachments"] == ["notes.txt"]


def test_multiple_attachments(db, kdbx_path, sample_file):
    a = sample_file("a.txt", b"aaa")
    b = sample_file("b.txt", b"bbb")
    secret, changed = secret_writer.secret_write(
        secret_path="mysecret", db=db, db_path=kdbx_path,
        attachments=[{"path": a}, {"path": b}],
    )
    assert sorted(secret["mysecret"]["attachments"]) == ["a.txt", "b.txt"]


def test_missing_secret_path_raises(db, kdbx_path):
    with pytest.raises(ValueError):
        secret_writer.secret_write(secret_path="", db=db, db_path=kdbx_path)
