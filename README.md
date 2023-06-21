Fast Servo Firmware and Software development
=========================================================================================

This repo contains all that you need to get started with Fast Servo platform. This document is meant to guide the user through the process of building, configuring hardware and booting Linux OS on the Fast Servo platform. However, before powering up the board, the following stages need to be completed (not an exhaustive list):
  * create block design and generate XSA file for the board
  * download and build Linux components
  * generate actual gateware that will be loaded onto the board
  * download and build Ubuntu filesystem
  * format and flash SD card.

At the end of the process you will get the general idea of what the gateware is capabable of, and what is not implemented yet. Please bear in mind, however, that this is only __development__ version and there is much room for improvement.

Although gateware generated from this repo allows to use Fast Servo platfrom on its own, it was developed with a particular need to be compatible with [Linien](https://github.com/linien-org/linien) application. Whenever this need has been embodied in code, it was clearly indicated in comments.

## Repo Structure

  * __block_design__ - contains board files, bash and TCL scripts needed to create XSA file
  * __builds__ - all build artifacts are placed there
  * __fast_servo__ - contains files used to create gateware and *pythonscripts*, which are used for chips configuration on a running board
  * __OS__ - contains all Ubuntu specific scripts and overlays

## Requirements

To build gateware:
  * PetalLinux
  * Xilinx Vivado
  * bootgen (usually installed together with Vivado)
  * [MiSoC](https://github.com/m-labs/misoc) and MiGen available (you can use pipenv with Pipfile)

***NOTE***: Both Petalinux and Vivado __MUST__ be in the same versions

***NOTE 2***: For development purposes version 2020.2 of Xilinx tools was used

Scripts used for Ubuntu building use _chroot_ and require _sudo_ priviliges. 

## Block design
***NOTE***: This step is only required if you want to generate everything from scratch. If you want to use XSA file provided with this repo, however, you can skip this step and move to **GATEWARE** section.

If you have Vivado available in your path, run from the ROOT of this repo:
``` 
$ ./block_design/build_block_design.sh
```

This step creates block design with Zynq and enables all interface and peripheral controllers needed by the Fast Servo platform. As a result _fast_servo_hw.xsa_ file is placed inside _builds_ directory.

***NOTE***: This step is a WORKAROUND and should be only temporary - configuration parameters are *HARDCODED* in TCL script, therefore changing them in HDL source code may not have an effect. In further work this should be generated from the HDL files, or 
skipped entirely.

## Gateware
Make sure you have MiSoC installed and available in your path. You can install it using pipenv and enter the pip virtual environment:
```
$ pipenv install
$ pipenv shell
```

There are two different gateware variants you can build - default one and the 'debug' one. The 'debug' variant has its ADC outputs hardwired (with clipping mechanism) to DAC inputs. (In the default variant you can still access the values, however, it is performed via low-performance CSRs). Having said the above, _BaseSoC_ from _fast_servo_soc.py_ is meant to be used - as its name indicates that - as a Base SoC for the user to subclass it. With this mechanism user's application is able to use ADC and DAC fast data lanes.

Assuming you have Vivado and MiSoC available in your path and you can build gateware with (from repo's ROOT): 
```
$ python -m fast_servo.gateware.fast_servo_soc [--debug]
```

As a result, script will generate, among others, _top.bit_, _top.bit.bin_ files. The first one is a bitstream, and the second one is the same bitstream, however, stripped of the headers and byte-swapped (as required by the FPGA manager tool).

## PetaLinux and Linux 
Assuming you have already installed and tested out correct Xilinx PetaLinux version, you can build needed OS components. 

During this step, you will need XSA file generated earlier (if you want to generate project from scratch, otherwise, you can use the XSA provided by this repo). PetaLinux project has been set up to boot from an SD Card and to use FPGA manager, instead of embedding bitstream in boot files. If you want to create the project from scratch, you have to run (remember to set up your project appropriately - even though PetaLinux does pretty decent job extracting information from XSA file, some things need to be opted in or out manually, such as boot options or FPGA Manager):
```
$ cd builds
$ petalinux-create -t project --template zynq --name [NAME_OF_YOUR_PROJECT]
$ cd petalinux-config --get-hw-description [PATH_TO_XSA_FILE]
```
Additionally, you need to enable the _SPIDEV_ user driver and _PRINTK_TIME_ in Kernel configs, as well as introduce some changes to generated devicetree (see in _recipes-kernel_ and _recipes-bsp_ in _builds/fast\_servo\_petalinux_ for reference):
```
$ petalinux-config -c kernel
$ petalinux-config -c u-boot
$ petalinux-build
```
However, if you want to go along with PetaLinux project already generated you can just run (assuming you are inside the this repo's root directory):
```
$ cd builds/fast_servo_petalinux
$ petalinux-config --get-hw-description ../fast_servo_hw.xsa --silentconfig
$ petalinux-build
```
and all of the changes to stock configuration should be applied automatically. The process might take a while and requires much disk space.

## FILESYSTEM
If you are happy to use Fast Servo with the filesystem PetaLinux provides, you can skip this step and move to **SD CARD** section. However, Linien uses Ubuntu specific commands and packages (this means it uses apt package manager instead of what Petalinux provides - dnf), therfore almost all development efforts were put into supporting Ubuntu file system (there were some trials with dnf, but it turned out to be too cumbersome to invest time and resources in it).

Assuming you have root priviliges and are inside the repo's root directory, run:
```
$ ./build_ubuntu.sh
```

This will download Ubuntu minimal tarball and patch it to meet the needs of Fast Servo platform (i.e. it copies python scripts that are used for platform configuration after boot). Additionally it installs packages to the OS image on user's machine, so the process doesn't need to be run on relatively slow Fast Servo hardware. As a result, a tarball __fastservo_os.tar.gz__ should be placed in _builds_ directory.

## SD Card
Follow [this](https://xilinx-wiki.atlassian.net/wiki/spaces/A/pages/18841655/Prepare+Boot+Medium) steps to prepare SD card for flashing. However, don't copy anything yet!

Having prepared SD card, mount both partitions (for the purpose of this document, it will be assumed that boot partition is mounted to _/tmp/BOOT_ and filesystem parition to _/tmp/rootfs_).

Before flashing your SD Card you need to generate boot components first. Assuming PetaLinux is available in your path, run:
```
$ cd builds/fast_servo_petalinux
$ petalinux-package --boot --fsbl --u-boot --force
```

Now you should be able to copy sources onto the SD card (assuming you are inside the root directory):
```
$ cp builds/fast_servo_petalinux/images/linux{BOOT.BIN,boot.scr,image.ub} /tmp/BOOT
$ tar xvf builds/fastservo_os.tar.gz -C /tmp/rootfs
$ sudo sync
```

You may copy generated bitstream (bin file) onto the SD card.

Now you can unmount the SD Card

## LAUNCHING

Before launch checklist:
  * configure *MODE* pins on Fast Servoto to ON position
  * connect to UART pins header (***NOT*** to USB on front panel)
  * open serial port console (i.e. minicom) with baud rate 115200 and turn the hardware flow control to OFF
  * power the device up - you should see on serial port logs
  * connect Fast Servo to your computer with Ethernet cable - make sure to either have DHCP server enabled or clicked "Shared to other computers" in your network manager 

After launching:
  * default login and password are "root:root"
  * either you can use the biststream from the SD card you copied above, or using for example _rsync_ copy the biststream now
  * run: `$ fpgautil -b [path_to_bitstream] -f Full`  to load your bistream on the FPGA
  * change directory to /root/pythonscripts and run: `$python3 initialize.py` to initialize Si5340, LTC2195 and AD9117 - ***UNFORTUNATELY THIS HAS TO BE RUN AT EVERY BOOT***
  * CONGRATS - you've just booted to Ubuntu Linux on your Fast Servo platform


## KNOWN ISSUES:
  * CSR addresses are hard-coded
  * on Fast Servo platform in _pythonscripts/common.py_ you need to manually comment/uncomment **LINIEN_OFFSET** variable. When you want to use Fast Servo on its own, offset should be set to 0x0, when you want to use Linien with Fast Servo - you need to set it to 0x300000
  * no support for USB on the front panel yet
  * spidev by default does not allow more than 3 devices on one SPI bus, so even though in devicetree AUX DAC is placed, there is no support for communication with it using SPIDEV at the moment
