#!/usr/bin/env python3
# coding: utf-8

from docker import Client
import docker
import json, time, os, sys
import netifaces as ni
import redis

# default container lifetime = 600 seconds !
DEFAULT_EXPIRATION = os.getenv('DEFAULT_EXPIRATION', 600)
# If a redis server is defined in environment then we use it, otherwise assumed local
REDIS = os.getenv('REDIS', "localhost:6379")

# db = redis.Redis(REDIS)
db = redis.StrictRedis(
    host="redis-16783.c8.us-east-1-3.ec2.cloud.redislabs.com", 
    port=16783, password="password"
)

def get_ip_address(ifname):
    zerotier_ip = os.getenv('IP', ni.ifaddresses(ifname)[2][0]['addr'])
    print("Advertised ip address: %s" % zerotier_ip, file=sys.stderr)
    # try:  
    #     return os.environ["IP"]
    # except KeyError: 
    #     print("No IP environment variable set, defaulting to eth0")
    #     return ni.ifaddresses(ifname)[2][0]['addr']
    return zerotier_ip

# cli = Client(base_url='unix://var/run/docker.sock')
tls_config = docker.tls.TLSConfig(
  client_cert=('../certs/cert.pem', '../certs/key.pem'),
  verify='../certs/ca.pem'
)
cli = Client(base_url='tcp://172.99.77.220:2376', tls=tls_config)

def run(run_params):
    # first make sure the image has been pulled locally:
    try:
        print("Pulling image if necessary")
        res = cli.pull(run_params['image'])
        print(res, file=sys.stderr)
    except(Exception) as error:
        raise error

    # Turn the port list into a dict
    binded_ports = {k:None for i, k in enumerate(run_params['ports'])}

    # Create container and bind to random host ports 
    try:
        print("Creating container")
        container = cli.create_container(
		image=run_params['image'], 
		ports=run_params['ports'], 
		detach=True,
        	host_config=cli.create_host_config(port_bindings=binded_ports)
	)
    except(Exception) as error:
        raise error
    
    # And start it
    try:
        print("Starting container: "+container.get('Id'))
        cli.start(container=container.get('Id'))
    except(Exception) as error:
        raise error

    container_id      = container['Id']
    ts                = time.time()
    expiration_ts     = ts + float(DEFAULT_EXPIRATION)
    ip                = get_ip_address('eth0')
    inspection        = cli.inspect_container(container=container.get('Id'))
    # host_binded_ports = {k:v[0]['HostPort'] for k,v in inspection['NetworkSettings']['Ports'].items()}
    host_binded_ports= ""
    #db.set(container_id, expiration_ts)

    res = {"public_ip":ip, "binded_ports":host_binded_ports, "container_id":container_id, \
    "timestamp":ts, "expiration_timestamp":expiration_ts}

    print("This container was just launched to sea, a little bit of data to monitor it in the waves:")
    print(res, file=sys.stderr)

    return res

def ps():
    c = cli.containers()
    return c

def renew(containerID):
    # workaround to get away with terminated container 
    # extend only if 30 seconds are remaining for container 
    
    # check if container is still running 
    containers = ps()
    if containerID in containers:   
        db.incrby(containerID, DEFAULT_EXPIRATION)
        return True
    else: # return false. Said container not found in running list
        return False

def stop(id):
    cli.stop(id)
    print("Stopping container with id: %s" %id, file=sys.stderr)

def remove(id):
    pass

def logs(id, lines=10):
    pass

def inspect(id):
    return cli.inspect_container(id)


# Run tests:
# params = {"image":"nginx:latest","ports":[80,443]}
# print(run(run_params=params))
