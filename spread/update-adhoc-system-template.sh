#!/bin/bash

# Copyright 2025 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: Apache-2.0

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