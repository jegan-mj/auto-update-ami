import boto3
ec2_client = boto3.client('ec2')
autoscaling_client = boto3.client('autoscaling')

OptimusPrime_AMI = "ami-0e65ed16c9bf1abc7"

def describe(client,function,maxrecords,tag_name,tag_value):
    print("Hi",client,function,maxrecords,tag_name,tag_value)
    response = client.function(
    MaxRecords = maxrecords,
    Filters=[
        {
            'Name': 'tag:' + tag_name,
            'Values': [tag_value]
        },
    ]
    )
    while 'NextToken' in response:
        response = describe(client,function,maxrecords,tag_name,tag_value)
        return response
    
def action(values,client,function,it_data,data):
    for value in values:
        client.function({"it_data": value}, data)
        
#Filter launch templates by old AMI

response = describe(ec2_client,"describe_launch_templates",200,"ami-name","optimus-prime")
launch_template_ids = [values["LaunchTemplateId"] for values in response["LaunchTemplates"]]

#Change the new AMI and Create new launch template version

data1 = {"SourceVersion": "$Latest"}
action(launch_template_ids,ec2_client,"create_launch_template_version","LaunchTemplateId",data1)

#Filter auto-scaling groups using the launch template

response = describe(autoscaling_client,"describe_auto_scaling_groups",100)
auto_scaling_group_names = [value["AutoScalingGroupName"] for value in response["AutoScalingGroups"] if value["LaunchTemplate"]["LaunchTemplateId"] in launch_template_ids ]
print("Auto-scaling Groups with Old AMI: ",auto_scaling_group_names)

#Initiate refresh instance

data2 = {"Strategy": "Rolling", "Preferences":{"MinHealthyPercentage": 90,"InstanceWarmup": 300}}
action(auto_scaling_group_names,autoscaling_client,"start_instance_refresh","AutoScalingGroupName",data2)
print("AMI Updated")