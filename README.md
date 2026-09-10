# Ansible Collection - haemka.keepass

Ansible collection for reading and writing KeePass secrets.

## Credits

This is a fork of [hasnimehdi91.keepass](https://github.com/Black-Cockpit/keepass) by
Hasni Mehdi, which laid the groundwork for all three modules. This fork adds file
attachment support, fuller read/write field parity between the modules, and a test
suite, and fixes a couple of bugs (some of which were also contributed back upstream).

## How it works

The secret_reader, group_reader  and secret_writer helps on managing the secrets of a keepass database with the ability to integrate it in automated tasks.
## Installation

Requirements: `python 3`, `pykeepass==4.0.6`

    pip install 'pykeepass==4.0.6' --user
    ansible-galaxy collection install haemka.keepass

## Testing

    pip install -r requirements-dev.txt
    pytest

To check coverage, including the module-contract tests that run each module as a
subprocess:

    KEEPASS_TEST_COVERAGE=1 coverage run --parallel-mode -m pytest
    coverage combine
    coverage report -m

## Modules

---
- **Module** : `haemka.keepass.secret_reader`
  - `db_path`     : Path to KeePass file
  - `db_password` : Password of KeePass file
  - `secret_path` : Path to secret in of KeePass file
  - `extract_attachments_to` : If set, write the secret's attachments as files into this directory
  - `attachment_filenames` : Only used together with `extract_attachments_to`. If set, only attachments whose filename is in this list are extracted, instead of all of them.
  - Returns `secret`, a dict keyed by the secret's name, containing whichever of these are set on the entry:
    - `username`
    - `password`
    - `url`
    - one key per custom property, e.g. `secret_value.custom_properties.gender` on write comes back as `secret.<name>.gender`
    - `attachments`: list of attachment filenames
---
- **Module** : `haemka.keepass.group_reader`
  - `db_path`     : Path to KeePass file
  - `db_password` : Password of KeePass file
  - `group_path`  : Path to group in of KeePass file
  - `extract_attachments_to` : If set, write each entry's attachments as files into a subdirectory (named after the entry) of this directory
  - `attachment_filenames` : Only used together with `extract_attachments_to`. If set, only attachments whose filename is in this list are extracted, instead of all of them.
  - Returns `group`, a list of per-entry dicts with the same fields as `secret_reader`'s `secret` above
---
- **Module** : `haemka.keepass.secret_writer`
  - `db_path`       : Path to KeePass file
  - `db_password`   : Password of KeePass file
  - `secret_path`   : Path to secret in of KeePass file
  -  `secret_value` : Dictionary containing the secret data. If not provided a empty secret will be created.
  - `secret_value.username`: Secret username
  - `secret_value.password:`: Secret password
  - `secret_value.url:`: Secret password
  - `secret_value.custom_properties:`: Secret customer properties (key, value)
  - `secret_value.attachments:`: List of files to attach to the entry, each with `path` (file on the control node) and optional `filename` (defaults to the basename of `path`)
  -  `force`: If set to true the secret will be overridden, Default is false
  - Returns `secret`, a dict keyed by the secret's name, containing whichever of these are set on the entry:
    - `username`
    - `password`
    - `url`
    - one key per custom property, e.g. `secret_value.custom_properties.gender` comes back as `secret.<name>.gender`
    - `attachments`: list of attachment filenames
---

## Usage

#### Read single secret

```yaml
- name: Read secret
  hosts: all
  become: no
  connection: local
  tasks:
  - haemka.keepass.secret_reader:
      db_path: "secrets.kdbx"
      db_password: "password"
      secret_path: "foo/bar/secret"
    register: test
  - debug:
      msg: "{{ test.secret }}"
      
```

```bash
ansible-playbook playbook.yml
```
---

#### Read group secrets

```yaml
- name: Read group secrets
  hosts: all
  become: no
  connection: local
  tasks:
  - haemka.keepass.group_reader:
      db_path: "secrets.kdbx"
      db_password: "password"
      group_path: "foo/bar"
    register: test
  - debug:
      msg: "{{ test.group }}"
      
```

```bash
ansible-playbook playbook.yml
```
---

#### Write secret

```yaml
# Write secret to database
#
# Define secret
- set_fact:
    secret:
        username: "John"
        password: "Doe"
        custom_properties:
            gender: "Male"
        attachments:
            - path: "/home/user/.ssh/id_rsa"
              filename: "id_rsa"

# Write secret
- name: Write secret
  haemka.keepass.secret_writer:
    db_path: "keys.kdbx"
    db_password: "password"
    secret_path: "/foo/bar"
    secret_value: "{{ secret }}
    force: false
  register: created_secret
  
- debug: var=created_secret
```

```bash
ansible-playbook playbook.yml
```