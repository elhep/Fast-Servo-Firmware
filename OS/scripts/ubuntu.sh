#!/bin/bash

if [ $ROOT_DIR ]; then
    echo ROOT_DIR is "$ROOT_DIR"
else
    echo Error: ROOT_DIR is not set
    echo exit with error
    exit
fi


UBUNTU_BASE_VER=20.04.5
UBUNTU_BASE_TAR=ubuntu-base-${UBUNTU_BASE_VER}-base-armhf.tar.gz
UBUNTU_BASE_URL=http://cdimage.ubuntu.com/ubuntu-base/releases/${UBUNTU_BASE_VER}/release/${UBUNTU_BASE_TAR}

if [[ -f $UBUNTU_BASE_TAR ]]; then
    echo "Ubuntu tarball exists; no need to download."
else
    echo "Ubntu tarball not found, downloading..."
    curl -L $UBUNTU_BASE_URL -o $UBUNTU_BASE_TAR
fi

sudo chown root:root $UBUNTU_BASE_TAR
sudo chmod 664 $UBUNTU_BASE_TAR

sudo tar -zxf $UBUNTU_BASE_TAR --directory=$ROOT_DIR

OVERLAY=$OS_DIR/overlay

sudo cp /etc/resolv.conf         $ROOT_DIR/etc/
sudo cp /usr/bin/qemu-arm-static  $ROOT_DIR/usr/bin

export LC_ALL=en_US.UTF-8

####################
# APT settings
####################

sudo install -v -m 664 -o root -D $OVERLAY/etc/apt/apt.conf.d/99norecommends $ROOT_DIR/etc/apt/apt.conf.d/99norecommends

sudo chroot $ROOT_DIR <<- EOF_CHROOT

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get -y upgrade
apt-get install -y apt-utils

apt-get -y install --install-recommends linux-tools-generic-hwe-20.04 linux-headers-generic-hwe-20.04
apt-get -y install software-properties-common
EOF_CHROOT

####################
# locale and keyboard
# setting LC_ALL overides values for all LC_* variables, this avids complaints
# about missing locales if some of this variables are inherited over SSH
####################


sudo chroot $ROOT_DIR <<- EOF_CHROOT

export DEBIAN_FRONTEND=noninteractive

# this is needed by systemd services 'keyboard-setup.service' and 'console-setup.service'
DEBIAN_FRONTEND=noninteractive \
apt-get -y install console-setup

# setup locale
apt-get -y install locales
locale-gen en_US.UTF-8
update-locale LANG=en_US.UTF-8 LANGUAGE=en_US LC_ALL=en_US.UTF-8

# Debug log
locale -a
locale
cat /etc/default/locale
cat /etc/default/keyboard
EOF_CHROOT

sudo install -v -m 664 -o root -D $OVERLAY/etc/hostname  $ROOT_DIR/etc/hostname


####################
# timezone and fake HW time
####################

sudo chroot $ROOT_DIR <<- EOF_CHROOT

export DEBIAN_FRONTEND=noninteractive

# install fake hardware clock
apt-get -y install fake-hwclock


ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime
apt-get install -y tzdata
dpkg-reconfigure --frontend noninteractive tzdata

EOF_CHROOT


# the fake HW clock will be UTC, so an adjust file is not needed
#echo $MYADJTIME > $ROOT_DIR/etc/adjtime
# fake HW time is set to the image build time
DATETIME=`date -u +"%F %T"`
echo date/time = $DATETIME
sudo echo $DATETIME > $ROOT_DIR/etc/fake-hwclock.data

####################
# File System table
####################

sudo install -v -m 664 -o root -D $OVERLAY/etc/fstab  $ROOT_DIR/etc/fstab

####################
# run other scripts
####################

. $OS_DIR/scripts/dev_tools.sh
. $OS_DIR/scripts/networking.sh
. $OS_DIR/scripts/fastservo.sh

####################
# handle users
####################

# http://0pointer.de/blog/projects/serial-console.html

sudo install -v -m 664 -o root -D $OVERLAY/etc/securetty $ROOT_DIR/etc/securetty
# sudo install -v -m 664 -o root -D $OVERLAY/etc/systemd/system/serial-getty@ttyPS0.service $ROOT_DIR/etc/systemd/system/getty.target.wants/serial-getty@ttyPS0.service

sudo chroot $ROOT_DIR <<- EOF_CHROOT
echo root:root | chpasswd
EOF_CHROOT

####################
# cleanup
####################

sudo chroot $ROOT_DIR <<- EOF_CHROOT
apt-get clean
history -c
EOF_CHROOT

# remove ARM emulation
sudo rm $ROOT_DIR/usr/bin/qemu-arm-static


####################
# archiving image
####################

# create a tarball (without resolv.conf link, since it causes schroot issues)
sudo rm $ROOT_DIR/etc/resolv.conf
# recreate resolv.conf link
sudo ln -sf /run/systemd/resolve/resolv.conf $ROOT_DIR/etc/resolv.conf
sudo tar -cpzf fastservo_os.tar.gz --one-file-system -C $ROOT_DIR .

# one final sync to be sure
sudo sync
