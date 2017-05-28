Vagrant.configure(2) do |config|
  config.vm.provider "virtualbox" do |v|
    v.memory = 2048
    v.cpus = 2
  end

  config.vm.provision "shell",
      privileged: false,
      inline: <<-SHELL
          cd /vagrant
         ./run_tests.sh
      SHELL

  config.vm.define "ubuntu1604" do |xenial|
    xenial.vm.box = "ubuntu/xenial64"
  end

  config.vm.define "opensuse422" do |leap422|
    leap422.vm.box = "opensuse/openSUSE-42.2-x86_64"
  end

  config.vm.define "centos7" do |centos7|
    centos7.vm.box = "centos/7"
  end

end
