import yaml, os.path, boto3


def checkType(var,datatype):
	if type(var) == datatype:
		return True
	else:
		return False


def returnAvailbilityZones():
	ec2 = boto3.client('ec2')
	my_session = boto3.session.Session()
	my_region = my_session.region_name
	# Retrieves availability zones only for region of the ec2 object
	response = ec2.describe_availability_zones()
	zones=[]
	for zone in response['AvailabilityZones']:
		zones.append(zone['ZoneName'])
	return zones[0]


def getConfigs():
	legal_stanzas=['indexers', 'cluster-master', 'sh-cluster', 'deploy']
	required_attrs=['MaxCount', 'MinCount', 'ImageId']
	cfgFile="aws-create.yaml"

	if os.path.isfile(cfgFile):
		with open(cfgFile, 'r') as ymlfile:
		    cfg = yaml.load(ymlfile)
		stanzas=cfg.keys()

		# validate aws-create.yaml settings.
		for stanza in stanzas:
			if stanza not in legal_stanzas:
				print("error in aws-create.yaml - Illegal stanza found: %s.  Expected stanzas are: indexers, cluster-master, sh-cluster, deploy." % stanza)
				exit()
			else:
				params=cfg[stanza]
				if params:
					try:
						MaxCount, MinCount, ImageId = params['MaxCount'], params['MinCount'], params['ImageId']
						if not (checkType(MaxCount,int) and checkType(MinCount,int)) or (MinCount > MaxCount):
							print("error in aws-crate.yaml at %s stanza - Please ensure MaxCount and MinCount is int and MaxCount > MinCount" % stanza)
							print("MaxCount: %s, MinCount: %s" % (MaxCount,MinCount))
							exit()
						if not (checkType(ImageId,str)):
							print("error in aws-crate.yaml at %s stanza - Please ensure ImageId is string value" % stanza)
							print("ImageId: %s" % ImageId)
					except:
						print("error in aws-crate.yaml at %s stanza - Missing a required attribute: %s" % (stanza,required_attrs))
						exit()
	else:
		print("error! config file aws-crate.yaml does not exist.")
		exit()

	return cfg


def getAttrs(attrs):

	defaults={
	'BlockDeviceMappings': [{'DeviceName':'/dev/xvda','Ebs': {'VolumeSize': 8,'VolumeType': 'standard'}}],
	'Monitoring': {'Enabled': True},
	'Placement': {'AvailabilityZone':'', 'Tenancy':'default'},
	'SecurityGroups': ['indexers'],
	'EbsOptimized': False,
	'InstanceInitiatedShutdownBehavior': 'stop',
	'DryRun': False,
	'TagSpecifications': [{'ResourceType': 'instance','Tags': [{'Key': 'Name','Value': 'deploy'}]}],
	'InstanceType':'t2.micro',
	'MinCount': 0,
	'MaxCount': 0,
	'ImageId': 'ami-e689729e'}

	defaults['Placement']['AvailabilityZone']=returnAvailbilityZones()

	for key in defaults.keys():
		if key in attrs.keys():
			defaults[key]=attrs[key]

	return defaults



def createAWSiNstances(params):
	ec2 = boto3.resource('ec2')
	defaults=getAttrs(params)
	for stanza in params:
		attrs=params[stanza]
		instance_attrs=getAttrs(attrs)
		instances = ec2.create_instances(DryRun=instance_attrs['DryRun'], 
			TagSpecifications=instance_attrs['TagSpecifications'], 
			InstanceInitiatedShutdownBehavior=instance_attrs['InstanceInitiatedShutdownBehavior'], 
			BlockDeviceMappings=instance_attrs['BlockDeviceMappings'], 
			Monitoring=instance_attrs['Monitoring'], 
			Placement=instance_attrs['Placement'], 
			ImageId=instance_attrs['ImageId'], 
			EbsOptimized=instance_attrs['EbsOptimized'], 
			SecurityGroups=instance_attrs['SecurityGroups'], 
			InstanceType=instance_attrs['InstanceType'],
			MinCount=instance_attrs['MinCount'],
			MaxCount=instance_attrs['MaxCount']
		)

		for instance in instances:
			# Wait for the instance to enter the running state
			instance.wait_until_running()
			# Reload the instance attributes
			instance.load()
			print(instance.public_dns_name)



	

	




awscfgs=getConfigs()


createAWSiNstances(awscfgs)


			






