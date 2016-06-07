OpenStack-Ansible Galera Server
###############################

Ansible role to install and configure a Galera cluster powered by MariaDB

Default Variables
=================

.. literalinclude:: ../../defaults/main.yml
   :language: yaml
   :start-after: under the License.

Required Variables
==================

To use this role, define the following variables:

.. code-block:: yaml

    galera_root_password: secrete


Example Playbook
================

.. code-block:: yaml

    - name: Install galera server
      hosts: galera_all
      user: root
      roles:
        - { role: "galera_server" }
      vars:
        galera_root_password: secrete

