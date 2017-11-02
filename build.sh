#!/bin/bash

ALL_AWS_INSTANCES_UP=false
logs="logs"

run () {
# $args1 - file name
	echo "`date` starting: ansible-playbook ${1}.yml" >> $logs/ansible-pb-${1}.log
	ansible-playbook $1.yml >> $logs/ansible-pb-${1}.log
	echo "`date` completed: ansible-playbook aws.yml" >> $logs/ansible-pb-${1}.log
	echo "Completed $1 playbook with the following results:"
	grep ": \[" $logs/ansible-pb-${1}.log | cut -d: -f1 | sort | uniq -c

	if [ `ls $logs/*.log | wc -l` -lt 2 ]
		then
		echo "`date` starting: Get AWS instance details." >> $logs/boto3.log
		python bin/get-aws-instance-details.py
		cat /etc/ansible/hosts >> $logs/boto3.log
		echo "`date` completed: Get AWS instance details." >> $logs/boto3.log
	fi
} 



if [ -d $logs ]
	then
	rm -f $logs/*.log
else
	echo "$logs directory does not exist! exiting"
	exit
fi

run "aws" # execute aws ansible playbook

echo "`date` starting: verify ssh status on AWS instances." >> $logs/aws-instance-alive.log
while [ $ALL_AWS_INSTANCES_UP != true ] # loop until all instances can be accessed over ssh
do
	for instance in `grep "ec2" $logs/boto3.log | awk '{print $1}'`
	do
		nc -z $instance 22 
		if [ $? -eq 0 ]
			then
			ALL_AWS_INSTANCES_UP=true
			echo "ssh is successful on $instance" >> $logs/aws-instance-alive.log
		else
			ALL_AWS_INSTANCES_UP=false
			echo "ssh is refused on $instance" >> $logs/aws-instance-alive.log
			break
		fi
	done
done
echo "`date` completed: verify ssh status on AWS instances." >> $logs/aws-instance-alive.log

run "common"

run "cm"

run "indexer"

