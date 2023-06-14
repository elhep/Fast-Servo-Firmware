#!/bin/bash


set -x 

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

while ! ping -c 1 -W 1 8.8.4.4; do
   echo "Not connected to the internet! RedPitaya needs to access the internet in order to proceed with the installation."
   sleep 1
done

echo 'installing dependencies...'
# the server is started in a screen session
apt-get install -y screen

cd /tmp
mkdir linien

echo 'installing pyrp3...'
# install pyrp3
cd /tmp/linien
git clone https://github.com/linien-org/pyrp3.git
cd pyrp3
git checkout e6688ac
python3 setup.py install

echo 'building monitor...'
# build monitor shared library
cd monitor
make
cp libmonitor.so /usr/lib/

cd /tmp
rm -R /tmp/linien