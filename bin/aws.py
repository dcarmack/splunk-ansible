import yaml

  
ec2client = boto3.client('ec2')
response = ec2client.describe_instances()
for reservation in response["Reservations"]:
    for instance in reservation["Instances"]:
        # This will print will output the value of the Dictionary key 'InstanceId'
        dns=instance["PublicDnsName"]
        for tag in instance["Tags"]:
        	instance_type=tag["Value"]

        print "%s %s" % (dns,instance_type)
