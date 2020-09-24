import boto3
ec2_client = boto3.client('ec2')
autoscaling_client = boto3.client('autoscaling')

OptimusPrime_AMI = "ami-0e65ed16c9bf1abc7"
tag_name = "ami-name"
tag_value = "optimus-prime"

#Filter launch templates by old Otptimus Prime AMI
response = ec2_client.describe_launch_templates(
    MaxResults = 200,
    Filters=[
        {
            'Name': 'tag:' + tag_name,
            'Values': [tag_value]
        },
    ]
)
while 'NextToken' in response:
    response = ec2_client.describe_launch_templates(
    Filters=[
        {
            'Name': 'tag:' + tag_name,
            'Values': [tag_value]
        },
    ]
)
launch_template_ids = [values["LaunchTemplateId"] for values in response["LaunchTemplates"]]
print("Launch Template Ids with Old AMI: ",launch_template_ids)

#Change the new AMI and Create new launch template version
for values in launch_template_ids:
    ec2_client.create_launch_template_version(
        LaunchTemplateId= values,
        SourceVersion="$Latest",
        LaunchTemplateData={
            'ImageId': OptimusPrime_AMI
        }
        
    )

#Filter auto-scaling groups using the launch template Ids and with $latest version
response = autoscaling_client.describe_auto_scaling_groups(MaxRecords=100)
while 'NextToken' in response:
    response = autoscaling_client.describe_auto_scaling_groups()
auto_scaling_group_names = [value["AutoScalingGroupName"] for value in response["AutoScalingGroups"] if value["LaunchTemplate"]["LaunchTemplateId"] in launch_template_ids and value["LaunchTemplate"]["Version"] == "$Latest"]
print("Auto-scaling Groups with Old AMI: ",auto_scaling_group_names)

#Initiate refresh instance
for values in auto_scaling_group_names:
    autoscaling_client.start_instance_refresh(
        AutoScalingGroupName= values,
        Strategy='Rolling',
        Preferences={
        'MinHealthyPercentage': 90,
        'InstanceWarmup': 300
        }
    )
print("Updated AMI Initiated")