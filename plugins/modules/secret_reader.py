#!/usr/bin/python

# Copyright: (c) 2023, Hasni Mehdi <hasnimehdi@outlook.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

import os.path
import traceback
from ansible.module_utils.basic import AnsibleModule, missing_required_lib

__metaclass__ = type
LIB_IMP_ERR = None
try:
    from pykeepass import PyKeePass

    HAS_LIB = True
except (ModuleNotFoundError, NameError):
    HAS_LIB = False
    LIB_IMP_ERR = traceback.format_exc()

DOCUMENTATION = r'''
---
module: secret_reader

short_description: Keepass secret_reader module

version_added: "1.0.0"

description: This module read from keepass database and return a dumped dictionary for the secret.

options:
    db_path:
        description: Keepass database path.
        required: true
        type: str
    db_password:
        description: Keepass database password.
        required: true
        type: str
    secret_path:
        description: Keepass secret path.
        required: true
        type: str
    extract_attachments_to:
        description: If set, write the secret's attachments as files into this directory on the
            control node. The attachment filenames returned in the secret data can be joined with
            this path to locate the extracted files.
        required: false
        type: str
    attachment_filenames:
        description: Only used together with extract_attachments_to. If set, only attachments
            whose filename is in this list are extracted, instead of all of them.
        required: false
        type: list
        elements: str
author:
    - Hasni Mehdi (@hasnimehdi91) <hasnimehdi@outlook.com>
    - haemka (@haemka) <github@haemka.net>
'''

EXAMPLES = r'''
# Read secret
- name: Read secret
  haemka.keepass.secret_reader:
    db_path: "keys.kdbx"
    db_password: "password"
    secret_path: "/foo/bar"
  register: secret
- debug: var=secret

# Read secret and extract its attachments to disk
- name: Read secret and extract attachments
  haemka.keepass.secret_reader:
    db_path: "keys.kdbx"
    db_password: "password"
    secret_path: "/foo/bar"
    extract_attachments_to: "/tmp/bar_attachments"
  register: secret
- debug: var=secret

# Read secret and extract only specific attachments
- name: Read secret and extract one attachment
  haemka.keepass.secret_reader:
    db_path: "keys.kdbx"
    db_password: "password"
    secret_path: "/foo/bar"
    extract_attachments_to: "/tmp/bar_attachments"
    attachment_filenames:
      - "id_rsa"
  register: secret
- debug: var=secret
'''

RETURN = r'''
# These are the attributes that can be returned by the module.
changed:
    description: The state of the task.
    type: bool
    returned: always
failed:
    description: Indicate if the task failed
    type: bool
    returned: always
data:
    description: Secret data.
    path:
        description: Secret path
        type: str
    secret:
        description: Dictionary containing the secret data, including username, password,
            url, custom properties and attachment filenames when set.
        type: dic
        returned: always
    attachments_extracted_to:
        description: The directory attachments were written to, when extract_attachments_to was set.
        type: str
        returned: when extract_attachments_to is set
'''


def run_module():
    """
    Keepass secret_reader module
    Returns:
    """
    secret_dic = dict()

    # Keepass secret_reader module arguments
    module_args = dict(
        db_path=dict(type='str', required=True),
        db_password=dict(type='str', required=True, no_log=True),
        secret_path=dict(type='str', required=True),
        extract_attachments_to=dict(type='str', required=False),
        attachment_filenames=dict(type='list', elements='str', required=False),
    )

    # Keepass module result initialization
    result = dict(
        changed=True,
        secret=secret_dic,
        failed=False
    )

    # Keepass module initialization
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if not HAS_LIB:
        module.fail_json(msg=missing_required_lib("pykeepass"), exception=LIB_IMP_ERR)

    if module.params['attachment_filenames'] and not module.params['extract_attachments_to']:
        module.fail_json(msg="attachment_filenames requires extract_attachments_to to be set")

    # Return module result
    if module.check_mode:
        module.exit_json(**result)

    try:
        db_path = module.params['db_path']
        db_password = module.params['db_password']
        db = PyKeePass(filename=db_path, password=db_password)

        secret_dic = secret_to_dic(db, module.params['secret_path'], module.params['extract_attachments_to'],
                                   module.params['attachment_filenames'])
    except Exception as e:
        module.fail_json(msg="Failed to read keepass secret: {0}".format(str(e)), exception=traceback.format_exc())

    result['secret'] = secret_dic
    result['path'] = module.params['secret_path']
    if module.params['extract_attachments_to']:
        result['attachments_extracted_to'] = module.params['extract_attachments_to']

    # Exit with result
    module.exit_json(**result)


def secret_to_dic(db: PyKeePass, secret_path: str, extract_attachments_to: str = None,
                  attachment_filenames: list = None) -> dict:
    """
    Read secret from Keepass and convert it to a dic
    Args:
        db: Keepass database
        secret_path: Secret path
        extract_attachments_to: If set, write the secret's attachments as files into this directory
        attachment_filenames: If set, only extract attachments whose filename is in this list
    Returns: dic
    """

    # Init secret value
    secret = dict()

    # Check if path is not provided
    if secret_path is None or secret_path == '' or secret_path.isspace():
        raise ValueError("secret_path is required")
    path = secret_path.split("/")

    # Remove white spaces
    if path is not None and len(path) > 0:
        path = [e for e in path if e]
    else:
        return secret

    # Find secret
    entry = db.find_entries_by_path(path=path)

    # Check if secret does not exist
    if entry is None:
        return secret

    # Append secret key
    secret[path[-1]] = dict()

    # Append secret username, password and extra attributes
    if entry.username:
        secret[path[-1]]["username"] = entry.username
    if entry.password:
        secret[path[-1]]["password"] = entry.password
    if entry.url:
        secret[path[-1]]["url"] = entry.url
    if entry.custom_properties and type(entry.custom_properties) is dict:
        for k in entry.custom_properties:
            secret[path[-1]][k] = entry.custom_properties[k]
    if entry.attachments:
        secret[path[-1]]["attachments"] = [attachment.filename for attachment in entry.attachments]
        if extract_attachments_to:
            _extract_attachments(entry, extract_attachments_to, attachment_filenames)

    # Return secret
    return secret


def _extract_attachments(entry, directory: str, attachment_filenames: list = None) -> None:
    """
    Write an entry's attachments as files into the given directory
    Args:
        entry: Keepass entry
        directory: Destination directory on the control node
        attachment_filenames: If set, only extract attachments whose filename is in this list
    """
    os.makedirs(directory, exist_ok=True)
    for attachment in entry.attachments:
        if attachment_filenames and attachment.filename not in attachment_filenames:
            continue
        with open(os.path.join(directory, attachment.filename), 'wb') as f:
            f.write(attachment.data)


def main():
    """
    Execute keepass secret_reader module
    Returns:

    """
    run_module()


if __name__ == '__main__':
    """
    Module main
    """
    main()
