#!/bin/bash

# Check if exactly one argument was provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <allocate|discard>"
    exit 1
fi

SPREAD_SYSTEM_USERNAME=SPREAD_REPLACE_USERNAME
SPREAD_PASSWORD=SPREAD_REPLACE_PASSWORD

MODE=$1
case "${MODE}" in
    "allocate")
        sudo sed -i "s|#PasswordAuthentication yes|PasswordAuthentication yes|g" /etc/ssh/sshd_config
        sudo sed -i "s|KbdInteractiveAuthentication no|KbdInteractiveAuthentication yes|g" /etc/ssh/sshd_config
        sudo cp /etc/ssh/sshd_config.d/60-cloudimg-settings.conf /etc/ssh/sshd_config.d/60-cloudimg-settings.conf.bak || true
        sudo rm -f /etc/ssh/sshd_config.d/60-cloudimg-settings.conf || true
        sudo systemctl daemon-reload
        sudo systemctl restart ssh

        sudo useradd ${SPREAD_SYSTEM_USERNAME} --shell /bin/bash --create-home || true
        echo "${SPREAD_SYSTEM_USERNAME}:${SPREAD_PASSWORD}" | sudo chpasswd || true
        echo "${SPREAD_SYSTEM_USERNAME} ALL=(ALL) NOPASSWD:ALL " | sudo tee /etc/sudoers.d/99-${SPREAD_SYSTEM_USERNAME}-user || true
        ;;
    
    "discard")
        sudo userdel -f -r ${SPREAD_SYSTEM_USERNAME} || true
        sudo rm -f /etc/sudoers.d/99-${SPREAD_SYSTEM_USERNAME}-user || true
        sudo rm -f /etc/ssh/sshd_config.d/60-cloudimg-settings.conf || true
        sudo mv /etc/ssh/sshd_config.d/60-cloudimg-settings.conf.bak /etc/ssh/sshd_config.d/60-cloudimg-settings.conf || true
        sudo sed -i "s|KbdInteractiveAuthentication yes|KbdInteractiveAuthentication no|g" /etc/ssh/sshd_config
        sudo sed -i "s|PasswordAuthentication yes|#PasswordAuthentication yes|g" /etc/ssh/sshd_config
        ;;

    *)
        echo "Invalid mode: ${MODE}. Use 'allocate' or 'discard'."
        exit 1
        ;;
esac

exit 0