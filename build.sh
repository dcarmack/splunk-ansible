#!/bin/bash

ansible-playbook aws.yml

python bin/get-aws-instance-details.py

cat /etc/ansible/hosts

ansible-playbook common.yml

ansible-playbook cm.yml

ansible-playbook indexer.yml


