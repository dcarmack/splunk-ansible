
import boto3

ec2 = boto3.resource('ec2')



indexers = ec2.create_instances(
#Unknown parameter in input: "Tags", must be one of: BlockDeviceMappings, ImageId, InstanceType, Ipv6AddressCount, Ipv6Addresses, KernelId, KeyName, MaxCount, MinCount, Monitoring, Placement, RamdiskId, SecurityGroupIds, SecurityGroups, SubnetId, UserData, AdditionalInfo, ClientToken, DisableApiTermination, DryRun, EbsOptimized, IamInstanceProfile, InstanceInitiatedShutdownBehavior, NetworkInterfaces, PrivateIpAddress, ElasticGpuSpecification, TagSpecifications

    ImageId='ami-e689729e',
    MinCount=1,
    MaxCount=2,
    InstanceType='t2.medium',
    KeyName='dcarmack',
    SecurityGroups=['indexers','launch-wizard-15'],
    TagSpecifications=[{'ResourceType': 'instance','Tags': [{"Key": "Name", "Value": "indexers"}]}],
    DryRun = False
    )



for instance in indexers:
	# Wait for the instance to enter the running state
	instance.wait_until_running()
	# Reload the instance attributes
	instance.load()
	print(instance.public_dns_name)