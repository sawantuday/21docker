#!/usr/bin/env python3
# coding: utf-8

import flask
from flask import request, jsonify
from container import run as docker_run
from container import renew as docker_renew
#from two1.wallet import Wallet
#from two1.bitserv.flask import Payment
import yaml
import json
import os

# initializze wallet 
# TWO1_WALLET_MNEMONIC = os.environ.get("TWO1_WALLET_MNEMONIC")
# TWO1_USERNAME = os.environ.get("TWO1_USERNAME")
# WALLET = Two1Wallet.import_from_mnemonic(mnemonic=TWO1_WALLET_MNEMONIC)

app = flask.Flask(__name__)
#payment = Payment(app, Wallet())

app.config['DEBUG'] = os.getenv('DEBUG', False)

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route('/docker/test/',methods=['GET'])
def test():
    return "hello world";

@app.route('/docker/run/', methods=['GET', 'POST'])
#@payment.required(5000)
def run():
    image = request.args.get('image')
    tag = request.args.get('tag', 'latest')
    memory = request.args.get('mem', '256')
    ports = request.args.getlist('port')
    
    if image == None:
        raise InvalidUsage('You must specify an image name', status_code=422)

    try:
        image = image + ":" + tag
        params = {"ports":ports, "image":image, "mem":memory}
        container = docker_run(params)
        return jsonify(container)
    except(Exception) as error:
        print(str(error))
        raise InvalidUsage(str(error), status_code=500)

@app.route('/docker/stop', methods=['GET', 'POST'])
# @payment.required(5)
def stop():
    containerID=request.args.get('container_id')
    print("Stopping container: "+containerID)
    docker_stop(containerID)
    return 'Done'

@app.route('/docker/renew', methods=['GET', 'POST'])
# @payment.required(5000)
def renew():
    containerID=request.args.get('container_id')
    print("Extending time for container: "+containerID)
    res = docker_renew(containerID)
    if res:
        return {'success':True}
    else:
        return {'success':False}
    return 'Feature not implemented'

@app.route('/docker/log', methods=['GET', 'POST'])
# @payment.required(5)
def log():
    return 'Feature not implemented'
@app.route('/docker/check', methods=['GET', 'POST'])
# @payment.required(5)
def check():
    return 'Feature not implemented'

#@app.route('/docker/run2/', methods=['GET', 'POST'])
#@payment.required(5000)
#def run2():
#    run_params = request.get_json(silent=False)
#
#    if 'image' in run_params:
#        # check for image format being name:tag or docker-py pull will download all tags !
#        if str(run_params['image']).endswith(":"):
#            raise InvalidUsage('You must specify an image name AND tag.', status_code=422)
#        if ":" not in run_params['image']:
#            raise InvalidUsage('You must specify an image name AND tag.', status_code=422)
#        try:
#            container = docker_run(run_params)
#            return jsonify(container)
#        except(Exception) as error:
#            # print(str(error))
#            raise InvalidUsage(str(error), status_code=500)
#    else:
#        raise InvalidUsage('You must specify at the very least an image name AND tag.', status_code=422)

@app.route('/manifest')
def manifest():
    """Provide the app manifest to the 21 crawler.
    """
    with open('./manifest.yaml', 'r') as f:
        manifest = yaml.load(f)
    return json.dumps(manifest)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
