#!/bin/bash

REPO_DIR="$(realpath .)"
BUILDS_DIR="$(realpath builds)"
OS_DIR="$(realpath OS)"

ROOT_DIR=$BUILDS_DIR/fs_root
BOOT_DIR=$BUILDS_DIR/fs_boot

. $OS_DIR/run.sh
