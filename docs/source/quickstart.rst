.. ...........................................................................
.. © Copyright IBM Corporation 2020                                          .
.. ...........................................................................

Quickstart
==========

After installing the collection outlined in the  `installation`_ guide, you
can access the collection and the ansible-doc covered in the following topics:

.. _installation:
   installation.html

ibm.power_hmc
--------------

After the collection is installed, you can access the collection content for a
playbook by referencing the namespace ``ibm`` and the collection's fully
qualified name ``powervc``. For example:

.. code-block:: yaml

  - name: VM Capture Playbook
    hosts: all
    gather_facts: no
    vars:
     auth:
      auth_url: https://{{ PowerVC }}:5000/v3
      project_name: '{{ powervc_project }}'
      username: '{{ powervc_user }}'
      password: '{{ powervc_password }}'
      project_domain_name: Default
      user_domain_name: Default
    tasks:
       - name: Perform VM Capture Operations
         powervc.cloud.capture_vm:
            auth: "{{ auth }}"
            name: "ansible_vm"
            image_name: "test_Image"
            validate_certs: no
         register: result
       - debug:
            var: result


In Ansible 2.14.0, the ``collections`` keyword was added to reduce the need
to refer to the collection repeatedly. For example, you can use the
``collections`` keyword in your playbook:

.. code-block:: yaml

ansible-doc
-----------

Modules included in this collection provide additional documentation that is
similar to a UNIX-like operating system man page (manual page). This
documentation can be accessed from the command line by using the
``ansible-doc`` command.

Here's how to use the ``ansible-doc`` command after you install the
**IBM PowerVC collection**: ``ansible-doc ibm.powervc.capture_vm``

For more information on using the ``ansible-doc`` command, refer
to the `Ansible guide`_.

.. _Ansible guide:
   https://docs.ansible.com/ansible/latest/cli/ansible-doc.html#ansible-doc

Connection Method
-----------------

Ansible communicates with remote machines over the SSH protocol. By default, Ansible uses native OpenSSH and connects to remote machines and communicates from the control node via SSH tunnel.

In case of HMC collection, since HMC is a closed appliance solution, its restricted shell will not allow push-based execution model of Ansible. Hence , current ansible collection for HMC would work with local connection type using the connection plugin, executing commands via SSH without pushing the code to the managed HMC. 
