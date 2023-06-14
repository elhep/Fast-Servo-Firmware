#!/bin/bash

if [ $ROOT_DIR ]; then
    echo ROOT_DIR is "$ROOT_DIR"
else
    echo Error: ROOT_DIR is not set
    echo exit with error
    exit
fi


sudo chroot $ROOT_DIR <<- EOF_CHROOT

export DEBIAN_FRONTEND=noninteractive

apt-get -y install dbus udev curl wget

apt-get -y install git

apt-get -y install build-essential cmake nano

# python3
apt-get -y install \
    python3.8 python3.8-dev python3.8-venv python3-pip  \
    python3-distutils python3-scipy python3-numpy       \
    python3-setuptools python3-wheel python3-jinja2     \
    python3-pandas python3-matplotlib
update-alternatives --set python3 /usr/bin/python3.8
pip3 install meson smbus2

EOF_CHROOT
