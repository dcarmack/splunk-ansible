
import yaml, boto3

results={}  
ansible_user="ec2-user" 
ansible_ssh_private_key_file="~/.ssh/dcarmack.pem"
inventory_file="/Users/dcarmack/Documents/git/splunk-ansible/inventory/hosts"
ansible_vars="/Users/dcarmack/Documents/git/splunk-ansible/group_vars/dynamic"

#u'State': {u'Code': 16, u'Name': 'running'}
filter1={"Name":"instance-state-name","Values":["running"]}
filter2={"Name":"tag:generated_by","Values":["ansible"]}

ec2client = boto3.client('ec2')
response = ec2client.describe_instances(Filters=[filter1,filter2])

for reservation in response["Reservations"]:
	
	public_dns=[]
	private_dns=[]
	hostname=[]

	for instance in reservation["Instances"]:
		public_dns.append(instance["PublicDnsName"])
		private_dns.append(instance["PrivateDnsName"])
		hostname.append('ip-%s' % instance["PrivateIpAddress"])
		for x in instance['Tags']:
			if x['Key'] == "Name":
				instance_type=x['Value']

	results.update({instance_type:{'public_dns':public_dns,'private_dns':private_dns,'hostname':hostname}})


def createInventoryFile(inventory_file):
	inventory_file=open(inventory_file,'w')
	inventory_file.write("[localhost]\nlocalhost ansible_connection=local ansible_python_interpreter=python\n\n")

	for each in results:
		inventory_file.write('[%s]\n' % each)
		for dns in results[each]['public_dns']:
			inventory_file.write('%s ansible_user=%s ansible_ssh_private_key_file=%s\n' % (dns,ansible_user,ansible_ssh_private_key_file))
		inventory_file.write("\n")

	inventory_file.close()


def updateYaml(value,file):
	cm_private_dns = value['cluster-master']['private_dns'][0]
	hostname=value['cluster-master']['hostname'][0].replace(".","-")
	f=open(file,'w')
	f.write("---\n")
	f.write("cm_private_dns: %s\n" % (cm_private_dns))
	f.write("app_loc: '{{ \"master-apps\" if ansible_hostname == \"%s\" else \"deployment-apps\" }}'\n" % hostname)
	f.write("app_loc_outputs: '{{ \"apps\" if ansible_hostname == \"%s\" else \"deployment-apps\" }}'\n" % hostname)
	f.close()




updateYaml(results,ansible_vars)

createInventoryFile(inventory_file)



