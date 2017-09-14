===============================
OpenStack-Ansible Galera server
===============================

Ansible role to install and configure a Galera cluster powered by MariaDB

To clone or view the source code for this repository, visit the role repository
for `galera_server <https://github.com/openstack/openstack-ansible-galera_server>`_.

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

External Restart Hooks
~~~~~~~~~~~~~~~~~~~~~~

When the role performs a restart of the mariadb service, it will notify an
Ansible handler named ``Manage LB``, which is a noop within this role. In the
playbook, other roles may be loaded before and after this role which will
implement Ansible handler listeners for ``Manage LB``, that way external roles
can manage the load balancer endpoints responsible for sending traffic to the
MariaDB servers being restarted by marking them in maintenance or active mode,
draining sessions, etc. For an example implementation, please reference the
`ansible-haproxy-endpoints role <https://github.com/Logan2211/ansible-haproxy-endpoints>`_
used by the openstack-ansible project.
