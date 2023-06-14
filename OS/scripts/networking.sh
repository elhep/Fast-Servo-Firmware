#!/bin/bash

if [ $ROOT_DIR ]; then
    echo ROOT_DIR is "$ROOT_DIR"
else
    echo Error: ROOT_DIR is not set
    echo exit with error
    exit
fi

sudo install -v -m 664 -o root -D $OVERLAY/etc/systemd/network/wired.network                $ROOT_DIR/etc/systemd/network/wired.network
sudo install -v -m 664 -o root -D $OVERLAY/etc/systemd/system/ssh-reconfigure.service       $ROOT_DIR/etc/systemd/system/ssh-reconfigure.service

sudo chroot $ROOT_DIR <<- EOF_CHROOT

export DEBIAN_FRONTEND=noninteractive

# network tools
apt-get -y install iproute2 iputils-ping curl

# SSH
apt-get -y install apt-transport-https ca-certificates openssh-server ssh
update-ca-certificates

# SSH access - enable SSH access to the root user
sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
# remove SSH keys, so they can be created at boot by ssh-reconfigure.service
/bin/rm -v /etc/ssh/ssh_host_*


# enable systemd network related services
systemctl enable systemd-networkd.service
systemctl enable systemd-resolved.service
systemctl enable systemd-timesyncd.service

# enable service for creating SSH keys on first boot
systemctl enable ssh-reconfigure.service


EOF_CHROOT