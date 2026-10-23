#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}

DOCUMENTATION = """
---
module: raid_configuration
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Manage PowerVC RAID configuration using chpvc raid and pvcraid
description:
  - This module manages PowerVC RAID configuration via two CLI entry points.
  - Use C(action=enable) or C(action=disable) to enable or disable the C(pvcraid)
    command using C(chpvc raid enable|disable).
  - Once C(pvcraid) is enabled, set C(subcommand) to the desired C(pvcraid) top-level
    command. Most subcommands require a further C(operation) value that maps to a
    C(pvcraid <subcommand> <operation>) sub-subcommand.
  - C(action) and C(subcommand) are mutually exclusive — only one may be provided
    per task.
notes:
  - C(pvcraid) must be enabled via C(action=enable) before any subcommand can
    be executed.
  - C(md_uuid) and C(alias) accept lists; the module repeats the flag for each item.
  - For C(grub rewrite-normal-boot) and C(grub set-bootline), pass all MD array
    UUIDs in C(md_uuid) — each is emitted as a separate C(--md-uuid) argument.
  - For C(mdadmconf write), pass all arrays in C(arrays) — each is emitted as a
    separate C(--array DEVICE UUID) argument.
  - For C(multipath write-bindings), pass all alias/WWID pairs in C(aliases) —
    each is emitted as a separate C(--alias ALIAS WWID) argument.
  - For C(rmdir run) and C(umount run), pass all directories/mountpoints in
    C(dirs) / C(mountpoints) respectively.
  - For C(rsync run), pass extra exclude patterns in C(excludes).
options:
  login_host:
    description:
      - IP address of the PowerVC Controller.
    required: true
    type: str
  login_user:
    description:
      - SSH user (C(pvcroot)).
    required: true
    type: str
  login_password:
    description:
      - Password for the SSH user.
    required: true
    type: str
  action:
    description:
      - C(enable) runs C(chpvc raid enable) to activate the C(pvcraid) command.
      - C(disable) runs C(chpvc raid disable) to deactivate the C(pvcraid) command.
      - Mutually exclusive with C(subcommand).
    required: false
    type: str
    choices: ['enable', 'disable']
  subcommand:
    description:
      - The C(pvcraid) top-level subcommand to execute.
      - Mutually exclusive with C(action).
    required: false
    type: str
    choices:
      - diskshow
      - dracut
      - grub
      - imgbackup
      - lvmconf
      - mdadmconf
      - mount
      - multipath
      - raidconf
      - rmdir
      - rsync
      - sync
      - umount
  operation:
    description:
      - Sub-subcommand (second positional argument) for subcommands that require one.
      - C(diskshow) — C(list), C(write), C(rescan).
      - C(dracut) — C(build).
      - C(grub) — C(mkconfig), C(set-devrootfs), C(rewrite-fs-uuid),
        C(rewrite-normal-boot), C(verify), C(set-bootline).
      - C(imgbackup) — C(run).
      - C(lvmconf) — C(update).
      - C(mdadmconf) — C(write).
      - C(mount) — C(run).
      - C(multipath) — C(configure), C(write-bindings).
      - C(raidconf) — C(create).
      - C(rmdir) — C(run).
      - C(rsync) — C(run).
      - C(sync) — C(run).
      - C(umount) — C(run).
    required: false
    type: str
  # ---------- dracut build ----------
  image:
    description:
      - Output initramfs image path (e.g. C(/boot/img3a)).
      - Required for C(subcommand=dracut, operation=build).
    required: false
    type: str
  kernel:
    description:
      - Kernel version string (e.g. output of C(uname -r)).
      - Required for C(subcommand=dracut, operation=build) and
        C(subcommand=imgbackup, operation=run).
    required: false
    type: str
  # ---------- grub mkconfig ----------
  mountpoint:
    description:
      - Chroot / mount directory used by several C(grub) operations and C(mount run).
      - Required for C(grub mkconfig).
      - Optional for C(grub rewrite-fs-uuid) and C(grub rewrite-normal-boot).
    required: false
    type: str
  output:
    description:
      - Output path for grub.cfg inside the chroot
        (default on device: C(/boot/grub2/grub.cfg)).
      - Optional for C(grub mkconfig).
    required: false
    type: str
  # ---------- grub set-devrootfs / set-bootline / verify ----------
  device:
    description:
      - New DEVROOTFS value (e.g. C(/dev/md0)).
      - Required for C(grub set-devrootfs).
      - Optional for C(mount run) — use instead of C(source) for device mounts.
    required: false
    type: str
  grub_cfg:
    description:
      - Path to C(grub.cfg) (default: C(/boot/grub2/grub.cfg)).
      - Optional for C(grub set-devrootfs), C(grub verify), and C(grub set-bootline).
    required: false
    type: str
  # ---------- grub rewrite-fs-uuid / rewrite-normal-boot ----------
  grub_d_dir:
    description:
      - Source grub.d directory (default: C(/etc/grub.d)).
      - Optional for C(grub rewrite-fs-uuid) and C(grub rewrite-normal-boot).
    required: false
    type: str
  md_uuid:
    description:
      - List of MD array UUIDs.
      - Each entry is emitted as a separate C(--md-uuid UUID) argument.
      - Required for C(grub rewrite-normal-boot) and C(grub set-bootline).
    required: false
    type: list
    elements: str
  settle_timeout:
    description:
      - C(rd.udev.settle-timeout) value in seconds (default on device: C(60)).
      - Optional for C(grub rewrite-normal-boot) and C(grub set-bootline).
    required: false
    type: int
  # ---------- grub set-bootline ----------
  grub_image:
    description:
      - Boot image to match and replace (e.g. C(/boot/img2a)).
      - Required for C(grub set-bootline).
    required: false
    type: str
  # ---------- mdadmconf write ----------
  arrays:
    description:
      - List of dicts, each with keys C(device) and C(uuid), representing MD arrays.
      - Each entry is emitted as C(--array DEVICE UUID).
      - Required for C(mdadmconf write).
      - Example: C([{device: /dev/md0, uuid: "abc:def:123:456"}]).
    required: false
    type: list
    elements: dict
  mailaddr:
    description:
      - MAILADDR entry for C(/etc/mdadm.conf) (default on device: C(root@localhost)).
      - Optional for C(mdadmconf write).
    required: false
    type: str
  # ---------- mount run ----------
  source:
    description:
      - Source for bind or filesystem-type mounts (e.g. C(/dev), C(proc), C(sysfs)).
      - Optional for C(mount run) — use instead of C(device) for bind/type mounts.
    required: false
    type: str
  bind:
    description:
      - Use the C(--bind) flag for the mount.
      - Optional for C(mount run).
    required: false
    type: bool
    default: false
  fstype:
    description:
      - Filesystem type passed as C(-t FSTYPE) (e.g. C(proc), C(sysfs)).
      - Optional for C(mount run).
    required: false
    type: str
  # ---------- multipath configure ----------
  polling_interval:
    description:
      - C(polling_interval) in C(defaults{}) (default on device: C(30)).
      - Optional for C(multipath configure).
    required: false
    type: int
  path_grouping_policy:
    description:
      - C(path_grouping_policy) (default on device: C(group_by_prio)).
      - Optional for C(multipath configure).
    required: false
    type: str
  path_selector:
    description:
      - C(path_selector) value (default on device: C("service-time 0")).
      - Optional for C(multipath configure).
    required: false
    type: str
  prio:
    description:
      - C(prio) value (default on device: C(alua)).
      - Optional for C(multipath configure).
    required: false
    type: str
  path_checker:
    description:
      - C(path_checker) value (default on device: C(tur)).
      - Optional for C(multipath configure).
    required: false
    type: str
  failback:
    description:
      - C(failback) value (default on device: C(immediate)).
      - Optional for C(multipath configure).
    required: false
    type: str
  features:
    description:
      - C(features) value (default on device: C("0")).
      - Optional for C(multipath configure).
    required: false
    type: str
  no_path_retry:
    description:
      - C(no_path_retry) value (default on device: C(fail)).
      - Optional for C(multipath configure).
    required: false
    type: str
  rr_weight:
    description:
      - C(rr_weight) value (default on device: C(priorities)).
      - Optional for C(multipath configure).
    required: false
    type: str
  rr_min_io_rq:
    description:
      - C(rr_min_io_rq) value (default on device: C(1)).
      - Optional for C(multipath configure).
    required: false
    type: int
  dev_loss_tmo:
    description:
      - C(dev_loss_tmo) in seconds (default on device: C(120)).
      - Optional for C(multipath configure).
    required: false
    type: int
  alias_prefix:
    description:
      - Alias prefix for each disk entry in C(multipaths{})
        (default on device: C(rootvg-disk)).
      - Optional for C(multipath configure).
    required: false
    type: str
  # ---------- multipath write-bindings ----------
  aliases:
    description:
      - List of dicts, each with keys C(alias) and C(wwid).
      - Each entry is emitted as C(--alias ALIAS WWID).
      - Required for C(multipath write-bindings).
      - Example: C([{alias: rootvg-disk1, wwid: "3600507681..."}]).
    required: false
    type: list
    elements: dict
  # ---------- raidconf create ----------
  raid_enabled:
    description:
      - Value for C(RAID_ENABLED) in the generated C(raid.conf) (C(true) or C(false)).
      - Required for C(raidconf create).
    required: false
    type: str
    choices: ['true', 'false']
  # ---------- rmdir run ----------
  dirs:
    description:
      - List of empty directories to remove.
      - Each entry is emitted as C(--dir DIR).
      - Required for C(rmdir run).
    required: false
    type: list
    elements: str
  # ---------- rsync run ----------
  rsync_source:
    description:
      - Source directory to sync (e.g. C(/) or C(/var/)).
      - Required for C(rsync run).
    required: false
    type: str
  rsync_dest:
    description:
      - Destination directory (e.g. C(/mnt/md0/)).
      - Required for C(rsync run).
    required: false
    type: str
  excludes:
    description:
      - List of additional exclude patterns (e.g. C(["/home/*"])).
      - Each entry is emitted as C(--exclude PATTERN).
      - Optional for C(rsync run).
    required: false
    type: list
    elements: str
  # ---------- umount run ----------
  mountpoints:
    description:
      - List of mountpoints to unmount, processed in the order given.
      - Pass in reverse-mount order (deepest first) when unmounting a chroot.
      - Each entry is emitted as C(--mountpoint MOUNTPOINT).
      - Required for C(umount run).
    required: false
    type: list
    elements: str
"""

EXAMPLES = """
---
# Example 1: Enable pvcraid command
- name: "RAID Configuration - Enable pvcraid"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Enable pvcraid command via chpvc raid enable"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        action: enable
      register: result
    - debug:
        var: result

# Example 2: Disable pvcraid command
- name: "RAID Configuration - Disable pvcraid"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Disable pvcraid command via chpvc raid disable"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        action: disable
      register: result
    - debug:
        var: result

# Example 3: List SCSI disk identifiers
- name: "RAID Configuration - diskshow list"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "List SCSI Disk Identifiers"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: diskshow
        operation: list
      register: result
    - debug:
        var: result

# Example 4: Write SCSI disk identifiers
- name: "RAID Configuration - diskshow write"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Write SCSI Disk Identifiers"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: diskshow
        operation: write
      register: result
    - debug:
        var: result

# Example 5: Rescan SCSI disks
- name: "RAID Configuration - diskshow rescan"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Rescan SCSI Disk Identifiers"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: diskshow
        operation: rescan
      register: result
    - debug:
        var: result

# Example 6: Build initramfs
- name: "RAID Configuration - dracut build"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Build initramfs with multipath, mdraid, lvm, and network support"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: dracut
        operation: build
        image: "{{ raid_dracut_image }}"
        kernel: "{{ raid_dracut_kernel }}"
      register: result
    - debug:
        var: result

# Example 7: Run grub2-mkconfig inside a chroot
- name: "RAID Configuration - grub mkconfig"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Run grub2-mkconfig inside a chroot"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: grub
        operation: mkconfig
        mountpoint: "{{ raid_mountpoint }}"
        output: "{{ raid_grub_output }}"
      register: result
    - debug:
        var: result

# Example 8: Replace DEVROOTFS in grub.cfg
- name: "RAID Configuration - grub set-devrootfs"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Replace DEVROOTFS in /boot/grub2/grub.cfg"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: grub
        operation: set-devrootfs
        device: "{{ raid_grub_device }}"
        grub_cfg: "{{ raid_grub_cfg }}"
      register: result
    - debug:
        var: result

# Example 9: Rewrite 39_powervc-fs-uuid script
- name: "RAID Configuration - grub rewrite-fs-uuid"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Rewrite 39_powervc-fs-uuid grub script"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: grub
        operation: rewrite-fs-uuid
        mountpoint: "{{ raid_mountpoint }}"
        grub_d_dir: "{{ raid_grub_d_dir }}"
      register: result
    - debug:
        var: result

# Example 10: Rewrite 41_powervc-normal-boot script
- name: "RAID Configuration - grub rewrite-normal-boot"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Rewrite 41_powervc-normal-boot grub script"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: grub
        operation: rewrite-normal-boot
        md_uuid: "{{ raid_md_uuid }}"
        settle_timeout: "{{ raid_settle_timeout }}"
        mountpoint: "{{ raid_mountpoint }}"
        grub_d_dir: "{{ raid_grub_d_dir }}"
      register: result
    - debug:
        var: result

# Example 11: Verify RAID boot parameters in grub.cfg
- name: "RAID Configuration - grub verify"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Verify RAID boot parameters in grub.cfg"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: grub
        operation: verify
        grub_cfg: "{{ raid_grub_cfg }}"
      register: result
    - debug:
        var: result

# Example 12: Replace kernel boot line in grub.cfg
- name: "RAID Configuration - grub set-bootline"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Replace kernel boot line with multipath and md.uuid parameters"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: grub
        operation: set-bootline
        grub_image: "{{ raid_grub_image }}"
        md_uuid: "{{ raid_md_uuid }}"
        settle_timeout: "{{ raid_settle_timeout }}"
        grub_cfg: "{{ raid_grub_cfg }}"
      register: result
    - debug:
        var: result

# Example 13: Backup boot images
- name: "RAID Configuration - imgbackup run"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Backup boot images and replace img2a with standard kernel"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: imgbackup
        operation: run
        kernel: "{{ raid_dracut_kernel }}"
      register: result
    - debug:
        var: result

# Example 14: Update LVM config to scan /dev/md
- name: "RAID Configuration - lvmconf update"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Add /dev/md to LVM scan and filter for RAID migration"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: lvmconf
        operation: update
      register: result
    - debug:
        var: result

# Example 15: Write /etc/mdadm.conf with array UUIDs
- name: "RAID Configuration - mdadmconf write"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Write /etc/mdadm.conf with MD array UUIDs"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: mdadmconf
        operation: write
        arrays: "{{ raid_arrays }}"
        mailaddr: "{{ raid_mailaddr }}"
      register: result
    - debug:
        var: result

# Example 16: Mount a device
- name: "RAID Configuration - mount run"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Mount a device to a mountpoint"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: mount
        operation: run
        device: "{{ raid_mount_device }}"
        mountpoint: "{{ raid_mountpoint }}"
      register: result
    - debug:
        var: result

# Example 17: Bind-mount a directory
- name: "RAID Configuration - mount run (bind)"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Bind-mount /dev into chroot"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: mount
        operation: run
        source: /dev
        mountpoint: "{{ raid_mountpoint }}"
        bind: true
      register: result
    - debug:
        var: result

# Example 18: Configure IBM 2145 Multipath
- name: "RAID Configuration - multipath configure"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Configure IBM 2145 Multipath"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: multipath
        operation: configure
        polling_interval: "{{ raid_polling_interval }}"
        alias_prefix: "{{ raid_alias_prefix }}"
      register: result
    - debug:
        var: result

# Example 19: Write multipath bindings file
- name: "RAID Configuration - multipath write-bindings"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Write /etc/multipath/bindings"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: multipath
        operation: write-bindings
        aliases: "{{ raid_aliases }}"
      register: result
    - debug:
        var: result

# Example 20: Create RAID configuration file
- name: "RAID Configuration - raidconf create"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Create /powervcdata/etc/raid/raid.conf"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: raidconf
        operation: create
        raid_enabled: "{{ raid_enabled }}"
      register: result
    - debug:
        var: result

# Example 21: Remove empty directories
- name: "RAID Configuration - rmdir run"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Remove empty directories"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: rmdir
        operation: run
        dirs: "{{ raid_dirs }}"
      register: result
    - debug:
        var: result

# Example 22: Rsync root filesystem to RAID destination
- name: "RAID Configuration - rsync run"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Rsync / to /mnt/md0/"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: rsync
        operation: run
        rsync_source: "{{ raid_rsync_source }}"
        rsync_dest: "{{ raid_rsync_dest }}"
        excludes: "{{ raid_excludes }}"
      register: result
    - debug:
        var: result

# Example 23: Flush filesystem buffers to disk
- name: "RAID Configuration - sync run"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Flush filesystem buffers to disk"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: sync
        operation: run
      register: result
    - debug:
        var: result

# Example 24: Unmount a chroot stack (deepest first)
- name: "RAID Configuration - umount run"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Unmount chroot mountpoints in reverse order"
      ibm.powervc.cli.raid_configuration:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        subcommand: umount
        operation: run
        mountpoints: "{{ raid_mountpoints }}"
      register: result
    - debug:
        var: result
"""

from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError
from ansible.module_utils.basic import AnsibleModule

# Subcommands that produce read-only/informational output (changed=False on success)
READ_ONLY_OPS = {
    ("diskshow", "list"),
    ("grub", "verify"),
}

# Required (subcommand, operation) pairs that need an explicit operation value
OPERATIONS_REQUIRED = {
    "diskshow": ["list", "write", "rescan"],
    "dracut": ["build"],
    "grub": ["mkconfig", "set-devrootfs", "rewrite-fs-uuid", "rewrite-normal-boot", "verify", "set-bootline"],
    "imgbackup": ["run"],
    "lvmconf": ["update"],
    "mdadmconf": ["write"],
    "mount": ["run"],
    "multipath": ["configure", "write-bindings"],
    "raidconf": ["create"],
    "rmdir": ["run"],
    "rsync": ["run"],
    "sync": ["run"],
    "umount": ["run"],
}


def construct_command(params):
    """
    Build the chpvc raid or pvcraid command string.
    Returns (command, messages).
    """
    messages = {}

    # ---- chpvc raid enable | disable ----
    if params.get("action"):
        return f"chpvc raid {params['action']}", messages

    sub = params["subcommand"]
    op = params.get("operation", "")

    # ---- diskshow ----
    if sub == "diskshow":
        return f"pvcraid diskshow {op}", messages

    # ---- dracut build ----
    if sub == "dracut":
        cmd = f"pvcraid dracut build --image {params['image']} --kernel {params['kernel']}"
        return cmd, messages

    # ---- grub ----
    if sub == "grub":
        cmd = f"pvcraid grub {op}"

        if op == "mkconfig":
            cmd += f" --mountpoint {params['mountpoint']}"
            if params.get("output"):
                cmd += f" --output {params['output']}"

        elif op == "set-devrootfs":
            cmd += f" --device {params['device']}"
            if params.get("grub_cfg"):
                cmd += f" --grub-cfg {params['grub_cfg']}"

        elif op == "rewrite-fs-uuid":
            if params.get("mountpoint"):
                cmd += f" --mountpoint {params['mountpoint']}"
            if params.get("grub_d_dir"):
                cmd += f" --grub-d-dir {params['grub_d_dir']}"

        elif op == "rewrite-normal-boot":
            for uuid in params["md_uuid"]:
                cmd += f" --md-uuid {uuid}"
            if params.get("settle_timeout") is not None:
                cmd += f" --settle-timeout {params['settle_timeout']}"
            if params.get("mountpoint"):
                cmd += f" --mountpoint {params['mountpoint']}"
            if params.get("grub_d_dir"):
                cmd += f" --grub-d-dir {params['grub_d_dir']}"

        elif op == "verify":
            if params.get("grub_cfg"):
                cmd += f" --grub-cfg {params['grub_cfg']}"

        elif op == "set-bootline":
            cmd += f" --image {params['grub_image']}"
            for uuid in params["md_uuid"]:
                cmd += f" --md-uuid {uuid}"
            if params.get("settle_timeout") is not None:
                cmd += f" --settle-timeout {params['settle_timeout']}"
            if params.get("grub_cfg"):
                cmd += f" --grub-cfg {params['grub_cfg']}"

        return cmd, messages

    # ---- imgbackup run ----
    if sub == "imgbackup":
        return f"pvcraid imgbackup run --kernel {params['kernel']}", messages

    # ---- lvmconf update ----
    if sub == "lvmconf":
        return "pvcraid lvmconf update", messages

    # ---- mdadmconf write ----
    if sub == "mdadmconf":
        cmd = "pvcraid mdadmconf write"
        for arr in params["arrays"]:
            cmd += f" --array {arr['device']} {arr['uuid']}"
        if params.get("mailaddr"):
            cmd += f" --mailaddr {params['mailaddr']}"
        return cmd, messages

    # ---- mount run ----
    if sub == "mount":
        cmd = f"pvcraid mount run --mountpoint {params['mountpoint']}"
        if params.get("device"):
            cmd += f" --device {params['device']}"
        if params.get("source"):
            cmd += f" --source {params['source']}"
        if params.get("bind"):
            cmd += " --bind"
        if params.get("fstype"):
            cmd += f" --type {params['fstype']}"
        return cmd, messages

    # ---- multipath ----
    if sub == "multipath":
        if op == "configure":
            cmd = "pvcraid multipath configure"
            if params.get("polling_interval") is not None:
                cmd += f" --polling-interval {params['polling_interval']}"
            if params.get("path_grouping_policy"):
                cmd += f" --path-grouping-policy {params['path_grouping_policy']}"
            if params.get("path_selector"):
                cmd += f" --path-selector \"{params['path_selector']}\""
            if params.get("prio"):
                cmd += f" --prio {params['prio']}"
            if params.get("path_checker"):
                cmd += f" --path-checker {params['path_checker']}"
            if params.get("failback"):
                cmd += f" --failback {params['failback']}"
            if params.get("features"):
                cmd += f" --features \"{params['features']}\""
            if params.get("no_path_retry"):
                cmd += f" --no-path-retry {params['no_path_retry']}"
            if params.get("rr_weight"):
                cmd += f" --rr-weight {params['rr_weight']}"
            if params.get("rr_min_io_rq") is not None:
                cmd += f" --rr-min-io-rq {params['rr_min_io_rq']}"
            if params.get("dev_loss_tmo") is not None:
                cmd += f" --dev-loss-tmo {params['dev_loss_tmo']}"
            if params.get("alias_prefix"):
                cmd += f" --alias-prefix {params['alias_prefix']}"
            return cmd, messages

        # write-bindings
        cmd = "pvcraid multipath write-bindings"
        for entry in params["aliases"]:
            cmd += f" --alias {entry['alias']} {entry['wwid']}"
        return cmd, messages

    # ---- raidconf create ----
    if sub == "raidconf":
        return f"pvcraid raidconf create --raid-enabled {params['raid_enabled']}", messages

    # ---- rmdir run ----
    if sub == "rmdir":
        cmd = "pvcraid rmdir run"
        for d in params["dirs"]:
            cmd += f" --dir {d}"
        return cmd, messages

    # ---- rsync run ----
    if sub == "rsync":
        cmd = f"pvcraid rsync run --source {params['rsync_source']} --dest {params['rsync_dest']}"
        for pat in (params.get("excludes") or []):
            cmd += f" --exclude {pat}"
        return cmd, messages

    # ---- sync run ----
    if sub == "sync":
        return "pvcraid sync run", messages

    # ---- umount run ----
    if sub == "umount":
        cmd = "pvcraid umount run"
        for mp in params["mountpoints"]:
            cmd += f" --mountpoint {mp}"
        return cmd, messages

    # Should never reach here — AnsibleModule choices validation catches unknown subcommands
    return "", messages


def _require(module, *param_names):
    """Fail if any of the named params are absent/empty."""
    missing = [n for n in param_names if not module.params.get(n)]
    if missing:
        module.fail_json(
            changed=False,
            failed=True,
            msg=f"The following parameters are required for this operation: {', '.join(missing)}.",
        )


def validate_params(module):
    """Cross-field validation beyond what AnsibleModule handles natively."""
    p = module.params
    sub = p.get("subcommand")
    op = p.get("operation")

    if not sub:
        return  # action path — no further validation needed

    # operation must be valid for the chosen subcommand
    valid_ops = OPERATIONS_REQUIRED.get(sub, [])
    if valid_ops and op not in valid_ops:
        module.fail_json(
            changed=False,
            failed=True,
            msg=(
                f"'operation' is required for subcommand '{sub}'. "
                f"Valid values: {valid_ops}."
            ),
        )

    # Per-operation required fields
    if sub == "dracut" and op == "build":
        _require(module, "image", "kernel")

    elif sub == "grub":
        if op == "mkconfig":
            _require(module, "mountpoint")
        elif op == "set-devrootfs":
            _require(module, "device")
        elif op in ("rewrite-normal-boot", "set-bootline"):
            _require(module, "md_uuid")
        if op == "set-bootline":
            _require(module, "grub_image")

    elif sub == "imgbackup" and op == "run":
        _require(module, "kernel")

    elif sub == "mdadmconf" and op == "write":
        _require(module, "arrays")
        for i, arr in enumerate(p.get("arrays") or []):
            if not arr.get("device") or not arr.get("uuid"):
                module.fail_json(
                    changed=False,
                    failed=True,
                    msg=f"arrays[{i}] must have both 'device' and 'uuid' keys.",
                )

    elif sub == "mount" and op == "run":
        _require(module, "mountpoint")
        if not p.get("device") and not p.get("source"):
            module.fail_json(
                changed=False,
                failed=True,
                msg="mount run requires at least one of: device, source.",
            )

    elif sub == "multipath" and op == "write-bindings":
        _require(module, "aliases")
        for i, entry in enumerate(p.get("aliases") or []):
            if not entry.get("alias") or not entry.get("wwid"):
                module.fail_json(
                    changed=False,
                    failed=True,
                    msg=f"aliases[{i}] must have both 'alias' and 'wwid' keys.",
                )

    elif sub == "raidconf" and op == "create":
        _require(module, "raid_enabled")

    elif sub == "rmdir" and op == "run":
        _require(module, "dirs")

    elif sub == "rsync" and op == "run":
        _require(module, "rsync_source", "rsync_dest")

    elif sub == "umount" and op == "run":
        _require(module, "mountpoints")


def run_cli_command():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type="str", required=True),
            login_user=dict(type="str", required=True),
            login_password=dict(type="str", required=True, no_log=True),
            action=dict(type="str", choices=["enable", "disable"]),
            subcommand=dict(
                type="str",
                choices=[
                    "diskshow", "dracut", "grub", "imgbackup", "lvmconf",
                    "mdadmconf", "mount", "multipath", "raidconf", "rmdir",
                    "rsync", "sync", "umount",
                ],
            ),
            operation=dict(type="str"),
            # dracut / imgbackup
            image=dict(type="str"),
            kernel=dict(type="str"),
            # grub (shared / per-op)
            mountpoint=dict(type="str"),
            output=dict(type="str"),
            device=dict(type="str"),
            grub_cfg=dict(type="str"),
            grub_d_dir=dict(type="str"),
            md_uuid=dict(type="list", elements="str"),
            settle_timeout=dict(type="int"),
            grub_image=dict(type="str"),
            # mdadmconf
            arrays=dict(type="list", elements="dict"),
            mailaddr=dict(type="str"),
            # mount
            source=dict(type="str"),
            bind=dict(type="bool", default=False),
            fstype=dict(type="str"),
            # multipath configure
            polling_interval=dict(type="int"),
            path_grouping_policy=dict(type="str"),
            path_selector=dict(type="str"),
            prio=dict(type="str"),
            path_checker=dict(type="str"),
            failback=dict(type="str"),
            features=dict(type="str"),
            no_path_retry=dict(type="str"),
            rr_weight=dict(type="str"),
            rr_min_io_rq=dict(type="int"),
            dev_loss_tmo=dict(type="int"),
            alias_prefix=dict(type="str"),
            # multipath write-bindings
            aliases=dict(type="list", elements="dict"),
            # raidconf
            raid_enabled=dict(type="str", choices=["true", "false"]),
            # rmdir
            dirs=dict(type="list", elements="str"),
            # rsync
            rsync_source=dict(type="str"),
            rsync_dest=dict(type="str"),
            excludes=dict(type="list", elements="str"),
            # umount
            mountpoints=dict(type="list", elements="str"),
        ),
        mutually_exclusive=[
            ["action", "subcommand"],
        ],
        required_one_of=[
            ["action", "subcommand"],
        ],
    )

    try:
        p = module.params

        validate_params(module)

        command, messages = construct_command(p)

        connection = Connection(
            module,
            p["login_host"],
            p["login_user"],
            p["login_password"],
            command=command,
            messages=messages,
        )

        rc, output = connection.run()

        # ---------------- NORMALIZE OUTPUT ----------------
        if isinstance(output, str):
            output = output.strip()

        output_list = output if isinstance(output, list) else [str(output)]
        rc = int(rc)

        # ---------------- FAILURE DETECTION ----------------
        failed = rc != 0

        # ---------------- CHANGED DETERMINATION ----------------
        if failed:
            changed = False
        elif p.get("action"):
            changed = True
        else:
            changed = (p["subcommand"], p.get("operation")) not in READ_ONLY_OPS

        # ---------------- RESULT ----------------
        result = dict(
            changed=changed,
            failed=failed,
            warning=False,
            stdout_lines=output_list,
            error="",
            rc=rc,
            msg="",
        )

        if failed:
            error_lines = [
                str(line).strip()
                for line in output_list
                if "error" in str(line).lower() or "Error" in str(line)
            ]
            result["msg"] = (
                error_lines[0]
                if error_lines
                else "raid_configuration command failed."
            )
            result["error"] = result["msg"]
        else:
            if p.get("action") == "enable":
                result["msg"] = "pvcraid command enabled successfully"
            elif p.get("action") == "disable":
                result["msg"] = "pvcraid command disabled successfully"
            else:
                op_label = f" {p['operation']}" if p.get("operation") else ""
                result["msg"] = f"pvcraid {p['subcommand']}{op_label} completed successfully"

        module.exit_json(**result)

    except (CLIError, Exception) as e:
        module.fail_json(changed=False, failed=True, msg=str(e))


def main():
    run_cli_command()


if __name__ == "__main__":
    main()
