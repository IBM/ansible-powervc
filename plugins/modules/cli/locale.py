#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: locale
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Manage PowerVC locale settings
description:
  - This module shows and modifies the locale on the PowerVC Controller
  - When C(locale_name) is omitted, the current locale is returned without changes
  - When C(locale_name) is provided, the locale is changed only if it differs from the current value (idempotent)
options:
  login_host:
    description:
      - IP address of the PowerVC Controller
    required: true
    type: str
  login_user:
    description:
      - SSH user (C(pvcroot))
    required: true
    type: str
  login_password:
    description:
      - Password for the SSH user
    required: true
    type: str
    no_log: true
  locale_name:
    description:
      - Target locale name (e.g. C(zh_SG.gbk) or C(en_US.UTF-8))
      - When omitted, the module only reports the currently enabled locale
    type: str
'''

EXAMPLES = '''
- name: Show current locale
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Get current locale setting
      ibm.powervc.cli.locale:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
      register: result

    - name: Display current locale
      debug:
        var: result.stdout_lines


- name: Modify locale
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Set locale to zh_SG.gbk
      ibm.powervc.cli.locale:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        locale_name: "zh_SG.gbk"
      register: result

    - name: Display locale change result
      debug:
        var: result.stdout_lines
'''

RETURN = '''
changed:
  description: Whether the locale was changed
  returned: always
  type: bool
stdout:
  description: Raw command output as a single string
  returned: always
  type: str
stdout_lines:
  description: Command output split into lines
  returned: always
  type: list
  elements: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
import re


def normalize_locale(value):
    if not value:
        return None

    value = value.strip()
    if " " in value:
        parts = value.split()
        if len(parts) == 2:
            value = f"{parts[0]}.{parts[1]}"

    value = value.lower()
    value = value.replace("utf-8", "utf8")

    return value


def extract_enabled_locale(text):
    match = re.search(
        r"Enabled locale:\s*([A-Za-z_]+)\s*([A-Za-z0-9_-]+)?", text)
    if not match:
        return None

    locale = match.group(1)
    encoding = match.group(2)

    if encoding:
        return f"{locale}.{encoding}"
    return locale


def canonicalize_locale(value, valid_locales):
    norm = normalize_locale(value)
    for loc in valid_locales:
        if normalize_locale(loc) == norm:
            return loc
    return None


def run_cmd(module, host, user, password, cmd):
    conn = Connection(module, host, user, password, command=cmd)
    rc, out = conn.run()

    if rc != 0:
        module.fail_json(msg=f"Command failed: {cmd}", stderr=out)

    if isinstance(out, list):
        return "\n".join(out), out

    return out, out


def result_ok(lines, changed=False, extra=None):
    result = {
        "changed": changed,
        "stdout": "\n".join(lines),
        "stdout_lines": lines
    }
    if extra:
        result.update(extra)
    return result


def clean_lines(lines):
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("+"):
            continue
        if "End of chpvc" in line:
            continue
        if "\x1b" in line:
            continue
        cleaned.append(line)
    return cleaned


def list_locales(module, host, user, password):
    _, lines = run_cmd(module, host, user, password, "chpvc locale list")
    return clean_lines(lines)


def handle_locale(module):
    host = module.params["login_host"]
    user = module.params["login_user"]
    password = module.params["login_password"]
    locale_name = module.params.get("locale_name")

    stdout, _ = run_cmd(module, host, user, password, "chpvc locale enabled")
    current_raw = extract_enabled_locale(stdout)

    if not current_raw:
        module.fail_json(msg="Unable to determine current locale")

    if not locale_name:
        return result_ok([current_raw], changed=False)

    valid_locales = list_locales(module, host, user, password)
    requested_canonical = canonicalize_locale(locale_name, valid_locales)

    if not requested_canonical:
        module.fail_json(
            msg=f"Invalid locale: {locale_name}",
            valid_locales=valid_locales
        )

    current_canonical = canonicalize_locale(current_raw, valid_locales)

    if normalize_locale(current_canonical) == normalize_locale(requested_canonical):
        return result_ok(
            [f"Locale already set to {current_canonical}"],
            changed=False
        )

    if module.check_mode:
        return result_ok(
            [f"[CHECK MODE] Would update locale to {requested_canonical}"],
            changed=True
        )

    run_cmd(
        module,
        host,
        user,
        password,
        f"chpvc locale modify {requested_canonical}"
    )

    return result_ok(
        [f"Locale updated to {requested_canonical}"],
        changed=True
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type="str", required=True),
            login_user=dict(type="str", required=True),
            login_password=dict(type="str", required=True, no_log=True),
            locale_name=dict(type="str")
        ),
        supports_check_mode=True
    )

    result = handle_locale(module)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
