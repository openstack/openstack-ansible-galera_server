OpenStack Galera Server
#######################
:tags: openstack, galera, server, cloud, ansible
:category: \*nix

Role for the installation and installation of a Galera Cluster powered by MariaDB

.. code-block:: yaml

    - name: Install galera server
      hosts: galera_all
      user: root
      roles:
        - { role: "galera_server", tags: [ "galera-server" ] }
      vars:
        container_address: "{{ ansible_ssh_host }}"
        galera_root_password: secrete
        galera_root_user: root
