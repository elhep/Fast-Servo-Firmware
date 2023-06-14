#!/bin/bash
set -x


# default image size if 3GB, which is appropriate for all 4BG SD cards
SIZE=3500

LOOPFILE=fastservo_loopfile


if [ $ROOT_DIR ]; then
    echo ROOT_DIR is "$ROOT_DIR"
else
    echo ROOT_DIR is not set
    echo setting ROOT_DIR to fs_root
    ROOT_DIR=fs_root

fi

if [ $BOOT_DIR ]; then
    echo BOOT_DIR is "$BOOT_DIR"
else
    echo BOOT_DIR is not set
    echo setting BOOT_DIR to fs_boot
    BOOT_DIR=fs_boot
fi


if [ $OS_DIR ]; then
    echo OS is "$OS_DIR"
else
    echo OS_DIR is not set
    echo setting OS_DIR to pwd
    OS_DIR=$(pwd)
fi

dd if=/dev/zero of=$LOOPFILE bs=1M count=$SIZE

DEVICE=`losetup -f`
sudo losetup $DEVICE $LOOPFILE

sudo parted -s $DEVICE mklabel msdos
sudo parted -s $DEVICE mkpart primary fat16   4MB 128MB
sudo parted -s $DEVICE mkpart primary ext4  128MB 100%

BOOT_DEV=/dev/`lsblk -lno NAME -x NAME $DEVICE | sed '2!d'`
ROOT_DEV=/dev/`lsblk -lno NAME -x NAME $DEVICE | sed '3!d'`


# Create file systems
sudo mkfs.vfat -v    $BOOT_DEV
sudo mkfs.ext4 -F -j $ROOT_DEV

# Mount file systems
mkdir -p $BOOT_DIR $ROOT_DIR
sudo mount $BOOT_DEV $BOOT_DIR
sudo mount $ROOT_DEV $ROOT_DIR

# mount binds
sudo mkdir -p $ROOT_DIR/dev $ROOT_DIR/sys $ROOT_DIR/proc $ROOT_DIR/dev/pts
sudo mount --bind /dev $ROOT_DIR/dev
sudo mount --bind /sys $ROOT_DIR/sys
sudo mount --bind /proc $ROOT_DIR/proc
sudo mount --bind /dev/pts $ROOT_DIR/dev/pts

# Run scripts

. $OS_DIR/scripts/ubuntu.sh 2>&1 | tee buildlog.txt

fuser -km $BOOT_DIR
fuser -km $ROOT_DIR
sleep 2

sudo umount $ROOT_DIR/{dev/pts,dev,sys,proc}
sudo umount $BOOT_DIR $ROOT_DIR
sleep 2

rmdir $BOOT_DIR $ROOT_DIR

sudo losetup -d $DEVICE
sudo rm $LOOPFILE
