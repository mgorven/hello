from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from itertools import chain
from time import sleep

import boto3
from fabric.api import task, env, sudo


elb_client = boto3.client('elb')
ec2_client = boto3.client('ec2')
instance_ids_by_host = {}

# Deploy with: fab web_hosts deploy


@task
def web_hosts():
    global instance_ids_by_host
    web_elb = elb_client.describe_load_balancers(LoadBalancerNames=['hello-elb'])
    instance_ids = [i['InstanceId'] for i in web_elb['LoadBalancerDescriptions'][0]['Instances']]
    reservations = ec2_client.describe_instances(InstanceIds=instance_ids)
    instances = chain(r['Instances'] for r in reservations['Reservations'])
    instance_ids_by_host.update({i['PublicDnsName']: i['InstanceId'] for i in instances})
    env.hosts = [i['PublicDnsName'] for i in instances]


@task
def deploy():
    # Remove from ELB to stop getting traffic
    elb_client.deregister_instances_from_load_balancer(
        LoadBalancerName='hello-elb',
        Instances=[{'InstanceId': instance_ids_by_host[env.host]}],
    )
    sudo('cd /home/web/hello && git fetch && git reset --hard origin/master')
    # Give ELB time to remove
    sleep(5)
    sudo('pkill -u web -INT flask')
    # Wait for active requests to finish
    sleep(5)
    sudo('/etc/rc.local')
    # Add back to ELB
    elb_client.register_instances_with_load_balancer(
        LoadBalancerName='hello-elb',
        Instances=[{'InstanceId': instance_ids_by_host[env.host]}],
    )
