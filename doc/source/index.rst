===============================
OpenStack-Ansible Galera server
===============================

Ansible role to install and configure a Galera cluster powered by MariaDB

Default variables
~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../defaults/main.yml
   :language: yaml
   :start-after: under the License.

Required variables
~~~~~~~~~~~~~~~~~~

To use this role, define the following variables:

.. code-block:: yaml

    galera_root_password: secrete


Example playbook
~~~~~~~~~~~~~~~~

.. literalinclude:: ../../examples/playbook.yml
   :language: yaml
