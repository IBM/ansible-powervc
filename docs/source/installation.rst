Installation
============

Steps to install Ansible:
==========================
Prerequisite:

1.	OS: Rhel 8.10

2.	Architecture: ppc64le



Step 1:

a. sudo dnf install -y ansible

b. ansible --version

You should now have Ansible installed and ready to use on your RHEL system.

Step 2: Installing from pip
If you prefer to install the ansible using pip, follow these steps:

Install Python and pip:

a. sudo dnf install python3 python3-pip

b. pip3 install ansible

c. ansible --version

Refer https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html and https://docs.ansible.com/ansible/latest/installation_guide/index.html 
for more details

OpenStack Ansible modules and PowerVC custom ansible modules use openstacksdk python libraries to perform operations in PowerVC. You must install OpenStack SDK before proceeding with the playbook execution. 

You can install the OpenStack SDK by using the pip install openstacksdk command.

Ansible does not contain the required collections and modules be default. You can run these commands to install OpenStack and PowerVC ansible collections.

=> pip3 install openstacksdk

=>	ansible-galaxy collection install openstack.cloud

=>	ansible-galaxy collection install ibm.powervc

Configure PowerVC Credentials to interact with Ansible
=======================================================

Auth information can be passed either in a config file or directly in the playbook.

1. Passing the auth info in a config file.

   Add the auth related information or credentials in the /etc/openstack/clouds.yaml. Example shown below:

   cat /etc/openstack/clouds.yml
   clouds:
     mycloud:
       auth:
         auth_url: https://<IP_ADDRESS_OF_POWERVC>>:5000/v3/
         username: USERNAME
         password: PASSWORD
         project_name: PROJECT_NAME
         project_domain_name: PROJECT_DOMAIN_NAME
         user_domain_name: USER_DOMAIN_NAME

Note: Auth information is driven by openstacksdk, which means that values can come from a yaml config file in /etc/ansible/openstack.yaml, /etc/openstack/clouds.yaml or ~/.config/openstack/clouds.yaml, then from standard environment variables, then finally by explicit parameters in plays. More information can be found at https://docs.openstack.org/openstacksdk/

2. Directly passing the credentials in the playbook.

You can refer the examples related to the aboves in each module playbook examples section.


===========================================================================
You can install the **IBM PowerVC collection** using one of these options:
Ansible Galaxy or a local build.

For more information on installing collections, see `using collections`_.

.. _using collections:
   https://docs.ansible.com/ansible/latest/user_guide/collections_using.html

Ansible Galaxy
--------------
Galaxy enables you to quickly configure your automation project with content
from the Ansible community.

Galaxy provides prepackaged units of work known as collections. You can use the
`ansible-galaxy`_ command with the option ``install`` to install a collection on
your system (control node) hosted in Galaxy.

By default, the `ansible-galaxy`_ command installs the latest available
collection, but you can add a version identifier to install a specific version.
Before installing a collection from Galaxy, review all the available versions.
Periodically, new releases containing enhancements and features you might be
interested in become available.

The ansible-galaxy command ignores any pre-release versions unless
the ``==`` range identifier is set to that pre-release version.
A pre-release version is denoted by appending a hyphen and a series of
dot separated identifiers immediately following the patch version. The
**IBM Power Systems HMC collection** releases collections with the pre-release
naming convention such as **1.0.0-beta1** that would require a range identifier.

Here is an example of installing a pre-release collection:

.. code-block:: sh

   $ ansible-galaxy collection install ibm.powervc:==1.0.0-beta1


If you have installed a prior version, you must overwrite an existing
collection with the ``--force`` option.

Here are a few examples of installing the **IBM PowerVC collection**:

.. code-block:: sh

   $ ansible-galaxy collection install ibm.powervc
   $ ansible-galaxy collection install -f ibm.powervc
   $ ansible-galaxy collection install --force ibm.powervc

The collection installation progress will be output to the console. Note the
location of the installation so that you can review other content included with
the collection, such as the sample playbook. By default, collections are
installed in ``~/.ansible/collections``; see the sample output.

.. _ansible-galaxy:
   https://docs.ansible.com/ansible/latest/cli/ansible-galaxy.html

.. code-block:: sh

   Process install dependency map
   Starting collection install process
   Installing 'ibm.power_hmc:1.0.0' to '/Users/user/.ansible/collections/ansible_collections/ibm/powervc'

After installation, the collection content will resemble this hierarchy: :

.. code-block:: sh

   ├── collections/
   │  ├── ansible_collections/
   │      ├── ibm/
   │          ├── powervc/
   │              ├── docs/
   │              ├── playbooks/
   │              ├── plugins/
   │                  ├── module_utils/
   │                  ├── modules/


You can use the `-p` option with `ansible-galaxy` to specify the installation
path, such as:

.. code-block:: sh

   $ ansible-galaxy collection install ibm.powervc -p /home/ansible/collections

When using the `-p` option to specify the install path, use one of the values
configured in COLLECTIONS_PATHS, as this is where Ansible itself will expect
to find collections.

For more information on installing collections with Ansible Galaxy,
see `installing collections`_.

.. _installing collections:
   https://docs.ansible.com/ansible/latest/user_guide/collections_using.html#installing-collections-with-ansible-galaxy


Local build
-----------

You can use the ``ansible-galaxy collection install`` command to install a
collection built from source. Version builds are available in the ``builds``
directory of the IBM ansible-power-hmc Git repository. The archives can be
installed locally without having to Galaxy.

To install a build from the ansible-power-hmc Git repository:

   1. Obtain a local copy from the Git repository:

      .. note::
         * Collection archive names will change depending on the release version.
         * They adhere to this convention **<namespace>-<collection>-<version>.tar.gz**, for example, **ibm-powervc-1.0.0.tar.gz**


   2. Install the local collection archive:

      .. code-block:: sh

         $ ansible-galaxy collection install ibm-powervc-1.0.0.tar.gz

      In the output of collection installation, note the installation path to access the sample playbook:

      .. code-block:: sh

         Process install dependency map
         Starting collection install process
         Installing 'ibm.powervc:1.0.0' to '/Users/user/.ansible/collections/ansible_collections/ibm/powervc'

      You can use the ``-p`` option with ``ansible-galaxy`` to specify the
      installation path, for example, ``ansible-galaxy collection install ibm-powervc-1.0.0.tar.gz -p /home/ansible/collections``.

      For more information, see `installing collections with Ansible Galaxy`_.

      .. _installing collections with Ansible Galaxy:
         https://docs.ansible.com/ansible/latest/user_guide/collections_using.html#installing-collections-with-ansible-galaxy
