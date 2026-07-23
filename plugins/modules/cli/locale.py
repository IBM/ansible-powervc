#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = """
---
module: locale
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Run chpvc locale utility
description:
  - This module modifies and shows the locale
options:
  login_host:
    description:
      - IP address of the PowerVC Controller
    required: true
    type: str
  login_user:
    description:
      - SSH User (pvcroot)
    required: true
    type: str
  login_password:
    description:
      - Password for the ssh user
    required: true
    type: str
  state:
    description:
      - Modifies or shows the locale
    required: true
    type: str
  locale_name:
    description:
      - Changes locale to the given value if the current locale is different
"""

EXAMPLE = """
---
- name: Run chpvc locale utility
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Show current locale"
      ibm.powervc.cli.locale:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: "present"
      register: result

    - name: "Display command output"
      debug:
        var: result.stdout_lines


---
- name: Run chpvc locale utility
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Modify locale"
      ibm.powervc.cli.locale:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: "present"
        locale_name: "zh_SG.gbk"
      register: result

    - name: "Display command output"
      debug:
        var: result.stdout_lines

"""

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


def handle_list(module, host, user, password):
    locales = list_locales(module, host, user, password)
    return result_ok(locales)


def handle_enabled(module, host, user, password):
    stdout, _ = run_cmd(module, host, user, password, "chpvc locale enabled")

    current = extract_enabled_locale(stdout)
    if current:
        return result_ok([current])

    return result_ok(["No enabled locale found"])


def handle_modify(module, host, user, password, locale_name):
    stdout, _ = run_cmd(module, host, user, password, "chpvc locale enabled")
    current_raw = extract_enabled_locale(stdout)
    valid_locales = list_locales(module, host, user, password)
    current_canonical = canonicalize_locale(current_raw, valid_locales)
    requested_canonical = canonicalize_locale(locale_name, valid_locales)

    if not requested_canonical:
        module.fail_json(
            msg=f"Invalid locale: {locale_name}",
            valid_locales=valid_locales
        )

    if normalize_locale(current_canonical) == normalize_locale(requested_canonical):
        return result_ok(
            [f"Locale already set to {current_canonical}"],
            changed=False
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


def handle_locale(module):
    host = module.params["login_host"]
    user = module.params["login_user"]
    password = module.params["login_password"]
    state = module.params["state"]
    locale_name = module.params.get("locale_name")

    if state != "present":
        module.fail_json(msg="Only 'present' state is supported")

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
            state=dict(type="str", required=True, choices=["present"]),
            locale_name=dict(type="str")
        ),
        supports_check_mode=False
    )

    result = handle_locale(module)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
