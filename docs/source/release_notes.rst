.. ...........................................................................
.. © Copyright IBM Corporation 2020                                          .
.. ...........................................................................

Releases
========

Version 1.0.0
-------------
Notes
  * Below are the IBM PowerVC modules included as part of version 1.0.0
  * capture_vm, clone_vm, manage_vm, unmanage_vm, migrate_vm, pin_vm, resize_vm, snapshot_vm, volume_attach, volume_detach, server, scg_operations, scg_info

Availability
  * `Galaxy v1.0.0`_
  * `GitHub v1.0.0`_

.. _Galaxy v1.0.0:
   https://galaxy.ansible.com/download/ibm-powervc-1.0.0.tar.gz

.. _GitHub v1.0.0:
   https://github.com/IBM/ansible-powervc/releases/download/v1.0.0/ibm-powervc-1.0.0.tar.gz

Version 1.1.0
-------------
Notes
  * Enabled the option to support SRIOV in server module.
  * volume_type_info, volume_type_update, copy_volume_type, all_volumes, manage_volume, unmanage_volume, snapshot_info storage modules are added as part of this version 1.1.0.
  
Availability
  * `Galaxy v1.1.0`_
  * `GitHub v1.1.0`_

.. _Galaxy v1.1.0:
   https://galaxy.ansible.com/download/ibm-powervc-1.1.0.tar.gz

.. _GitHub v1.1.0:
   https://github.com/IBM/ansible-powervc/releases/download/v1.1.0/ibm-powervc-1.1.0.tar.gz

Version 1.2.0
-------------
Notes
  * novalink_registration and hmc_registration registration modules are added.
  * host_maintenance and host_recall modules are added as part of this version 1.2.0.

Availability
  * `Galaxy v1.2.0`_
  * `GitHub v1.2.0`_

.. _Galaxy v1.2.0:
   https://galaxy.ansible.com/download/ibm-powervc-1.2.0.tar.gz

.. _GitHub v1.2.0:
   https://github.com/IBM/ansible-powervc/releases/download/v1.2.0/ibm-powervc-1.2.0.tar.gz

Version 1.3.0
-------------
Notes
  * consistency_group module is added for managing Consistency Groups in PowerVC.
  * group_action module is added to perform actions on Consistency Groups.
  * auxiliary_volume module is added to manage auxiliary volume onboarding jobs.
  * retype_volume module is added to perform retype operations on volumes.

Availability
  * `Galaxy v1.3.0`_
  * `GitHub v1.3.0`_

.. _Galaxy v1.3.0:
   https://galaxy.ansible.com/download/ibm-powervc-1.3.0.tar.gz

.. _GitHub v1.3.0:
   https://github.com/IBM/ansible-powervc/releases/download/v1.3.0/ibm-powervc-1.3.0.tar.gz

Version 1.4.0
-------------
Notes
  * CLI modules are introduced as a new category of modules that connect to the PowerVC Controller over SSH and execute PowerVC command-line operations.
  * CLI modules support operations such as backup, restore, configure, update, service management, and more.
  * All CLI modules use SSH-based authentication (login_host, login_user, login_password) via the pvcroot user.
  * pexpect is added as a dependency on the Ansible server to support interactive SSH command execution used by CLI modules.

Availability
  * `Galaxy v1.4.0`_
  * `GitHub v1.4.0`_

.. _Galaxy v1.4.0:
    https://galaxy.ansible.com/download/ibm-powervc-1.4.0.tar.gz

.. _GitHub v1.4.0:
    https://github.com/IBM/ansible-powervc/releases/download/v1.4.0/ibm-powervc-1.4.0.tar.gz

