#!/bin/bash

if [ $ROOT_DIR ]; then 
    echo ROOT_DIR is "$ROOT_DIR"
else
    echo Error: ROOT_DIR is not set
    echo exit with error
    exit
fi

####################
sudo chroot $ROOT_DIR <<- EOF_CHROOT
export DEBIAN_FRONTEND=noninteractive

# I2C libraries
apt-get install -y libi2c-dev i2c-tools

pip3 install spidev
apt-get install -y fpga-manager-xlnx
EOF_CHROOT


# UDEV rules setting hardware access group rights
sudo install -v -m 664 -o root -D $OVERLAY/etc/udev/rules.d/10-fastservo.rules      $ROOT_DIR/etc/udev/rules.d/10-fastservo.rules
sudo install -v -m 664 -o root -D $OVERLAY/etc/udev/rules.d/80-i2c-noroot.rules     $ROOT_DIR/etc/udev/rules.d/80-i2c-noroot.rules

sudo chroot $ROOT_DIR <<- EOF_CHROOT
export DEBIAN_FRONTEND=noninteractive

# add system groups for HW access
groupadd --system xdevcfg
groupadd --system uio
groupadd --system gpio
groupadd --system spi

# add a default user
useradd -m -c "FastServo" -s /bin/bash -G sudo,xdevcfg,uio,gpio,spi,i2c,dialout fastservo
EOF_CHROOT


sudo cp -r $REPO_DIR/fast_servo/pythonscripts    $ROOT_DIR/root
sudo chown -R root:root     $ROOT_DIR/root/pythonscripts
