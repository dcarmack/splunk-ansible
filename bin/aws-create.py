import yaml, os.path, boto3

from botocore.exceptions import ClientError

ec2 = boto3.client('ec2')


### security groups start ### 

security_groups={
	'splunk-web':{
		'description':'Allows access to Splunk web port.',
		'rules':[
			{'proto':'tcp','fport':8000,'tport':8000,'iprange':'0.0.0.0/0'}
		]
	},
	'indexers':{
		'description':'Opens management and splunktcp input port.',
		'rules':[
			{'proto':'tcp','fport':9997,'tport':9997,'iprange':'172.16.0.0/12'},
			{'proto':'tcp','fport':8089,'tport':8089,'iprange':'172.16.0.0/12'}
		]
	},
	'cluster-idx':{
		'description':'Opens replication port for indexer activity.',
		'rules':[
			{'proto':'tcp','fport':9887,'tport':9887,'iprange':'172.16.0.0/12'},
		]
	},
	'cluster-master':{
		'description':'Opens required ports for cluster master activity.',
		'rules':[
			{'proto':'tcp','fport':8089,'tport':8089,'iprange':'172.16.0.0/12'}
		]
	},
	'deploy':{
		'description':'Opens required ports for deployer/deployment server activity.',
		'rules':[
			{'proto':'tcp','fport':8089,'tport':8089,'iprange':'172.16.0.0/12'}
		]
	}
}


def checkSecurityGroupExists(group):
	try:
	    response = ec2.describe_security_groups(GroupNames=[group])
	    #print response['SecurityGroups']
	    return True

	except ClientError as e:
		return False


def createSecurityGroup(group,description,rules,vpc_id):
	try:
	    response = ec2.create_security_group(GroupName=group,Description=description,VpcId=vpc_id)
	    security_group_id = response['GroupId']
	    print('Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))
	    for rule in security_groups[group]['rules']:
		    data = ec2.authorize_security_group_ingress(
		        GroupId=security_group_id,
		        IpPermissions=[
		            {'IpProtocol': rule['proto'],
		             'FromPort': rule['fport'],
		             'ToPort': rule['tport'],
		             'IpRanges': [{'CidrIp': rule['iprange'] }]
		             } 
		         ])

		    print('Ingress Successfully Set %s' % data)


	except ClientError as e:
		print e
		exit()



def getSecurityGroups(group):
	# maps instance type to security group
	security_group_mapping={
		'indexer':['indexers'],
		'deploy':['splunk-web','deploy'],
		'cluster-master':['splunk-web','cluster-master'],
		'cluster-idx':['indexers','cluster-idx'],
		'search-head':['splunk-web']
		}
	return security_group_mapping[group]


### security groups end ### 





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
	# validates aws-create.yaml settings and returns yaml coonfiguration
	legal_stanzas=['indexer', 'cluster-idx', 'cluster-master', 'cluster-sh', 'deploy', 'search-head']
	required_attrs=['MaxCount', 'MinCount', 'ImageId']
	cfgFile="aws-create.yaml"

	if os.path.isfile(cfgFile):
		with open(cfgFile, 'r') as ymlfile:
		    cfg = yaml.load(ymlfile)
		stanzas=cfg.keys()

		# validate aws-create.yaml settings.
		for stanza in stanzas:
			if stanza not in legal_stanzas:
				print("error in %s - Illegal stanza found: %s.  Expected stanzas are: indexers, cluster-master, sh-cluster, deploy." % (cfgFile,stanza))
				exit()
			else:
				params=cfg[stanza]
				if params:
					try:
						MaxCount, MinCount, ImageId = params['MaxCount'], params['MinCount'], params['ImageId']
						if not (checkType(MaxCount,int) and checkType(MinCount,int)) or (MinCount > MaxCount):
							print("error in %s at %s stanza - Please ensure MaxCount and MinCount is int and MaxCount > MinCount" % (cfgFile,stanza))
							print("MaxCount: %s, MinCount: %s" % (MaxCount,MinCount))
							exit()
						if not (checkType(ImageId,str)):
							print("error in %s at %s stanza - Please ensure ImageId is string value" % (cfgFile,stanza))
							print("ImageId: %s" % ImageId)
					except:
						print("error in %s at %s stanza - Missing a required attribute: %s" % (cfgFile,stanza,required_attrs))
						exit()
	else:
		print("error! config file %s does not exist." % cfgFile)
		exit()

	return cfg






def getAttrs(stanza,attrs):
	response = ec2.describe_vpcs()
	vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
	sg=getSecurityGroups(stanza)
	for group in sg:
		rules=security_groups[group]['rules']
		description=security_groups[group]['description']
		if not checkSecurityGroupExists(group):
			createSecurityGroup(group,description,rules,vpc_id)



	defaults={
		'BlockDeviceMappings': [{'DeviceName':'/dev/xvda','Ebs': {'VolumeSize': 8,'VolumeType': 'standard'}}],
		'Monitoring': {'Enabled': True},
		'Placement': {'AvailabilityZone':returnAvailbilityZones(), 'Tenancy':'default'},
		'SecurityGroups': sg,
		'EbsOptimized': False,
		'InstanceInitiatedShutdownBehavior': 'stop',
		'DryRun': False,
		'TagSpecifications': [{'ResourceType': 'instance','Tags': [{'Key': 'Name','Value': stanza }]}],
		'InstanceType':'t2.micro',
		'MinCount': 0,
		'MaxCount': 0,
		'ImageId': 'ami-e689729e'}


	for key in defaults.keys():
		if key in attrs.keys():
			defaults[key]=attrs[key]

	return defaults



def createAWSiNstances(params):
	ec2 = boto3.resource('ec2')
	for stanza in params:
		attrs=params[stanza]
		instance_attrs=getAttrs(stanza,attrs)

		instances = ec2.create_instances(
			DryRun=instance_attrs['DryRun'], 
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

		print "test"
		for instance in instances:
			# Wait for the instance to enter the running state
			instance.wait_until_running()
			# Reload the instance attributes
			instance.load()
			print(instance.public_dns_name)








	


if __name__=="__main__":


	awscfgs=getConfigs()

	createAWSiNstances(awscfgs)


			






