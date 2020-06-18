#!/bin/sh
# This script copy the .ssh folder on the host (mounted in /root/.ssh_host)
# to the guest
# Usage:
#   docker run -v $HOME/.ssh:/root/.ssh_host -v alde_ssh:/root/.ssh ...
#   docker exec -it <container> copy_keys.sh
cp /root/.ssh_host/* /root/.ssh && chmod 700 /root/.ssh

