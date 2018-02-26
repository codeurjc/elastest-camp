import yaml

# To run these tests in ElasTest we need a project. Then, for each docker-compose file generated (i.e., for each configuration), we need: 
# 1. To create a SUT within the project configured with the corresponding docker-compose file (without the test container)
# 2. To create a TJob within the project that will make use of the SUT configured in step 1. This TJob will run the xwiki-test container (songhui/xwiki-smoke-client docker image) against the SUT defined in 1

# First we create the project
import requests
url = 'http://localhost:37000/api/project'
data = '''{
  "name": "CAMP",
  "tjobs": [],
  "id": 0,
  "suts": []
}'''
headers = {
    'Origin': 'http://localhost:37000',
    'content-type': 'application/json',
    'Referer': 'http://localhost:37000/'
}
response = requests.post(url, headers=headers, data=data)

print(response.status_code)
print(response.reason)
print(response.text)
print('####################################')


# The following steps shall be run for each docker-compose file

# Now we load the docker-compose file, and make some changes to adapt to the docker-compose format accepted by ElasTest's docker-compose agent
# We're using docker-compose-2.yml as docker-compose-1.yml doesn't work due to an unavailable image
with open("xwiki/docker-compose/docker-compose-2.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

# Remove test container (the test container will be configured in the TJob)
cfg['services'].pop('test', None)
# Remove container_name property (unsupported by ElasTest's docker-compose agent) and using its value instead as the service name
cfg['services']['web'].pop('container_name')
cfg['services']['xwiki-web'] = cfg['services'].pop('web')
# Same as above, but for the postgres service
cfg['services']['postgres'].pop('container_name')
cfg['services']['xwiki-postgres-db'] = cfg['services'].pop('postgres')
# The dependency name changes, as the postgres service is now named xwiki-postgres-db
cfg['services']['xwiki-web']['depends_on'] = ['xwiki-postgres-db']

print('####################################')


# Then, we create the SUT. For this, we use the modified docker-compose configuration, and specify the project to which the SUT belongs
data = """{
    "id": 0,
    "name": "docker-compose-2",
    "specification": "%s",
    "sutType": "MANAGED",
    "description": "docker-compose-2",
    "project": %s,
    "instrumentalize": false,
    "instrumentedBy": "WITHOUT",
    "port": "8080",
    "managedDockerType": "COMPOSE",
    "mainService": "xwiki-web",
    "parameters": [],
    "commands": "",
    "commandsOption": "DEFAULT"
}""" % (yaml.dump(cfg).replace('"', '\\"').replace("\n", "\\n"), response.text)
print(data)
response2 = requests.post('http://localhost:37000/api/sut', headers=headers, data=data)
print(response2.status_code)
print(response2.text)
print('####################################')


# Next, we create the TJob. 
# Ideally, we would configure as well the metrics and logs of the different components, but that would introduce a lot of burden in the json (the data variable)
# Instead, we can manually add them while the tjob is running or even after.
data = """{
  "id": 0,
  "name": "docker-compose-2",
  "imageName": "songhui/xwiki-smoke-client",
  "sut": %s,
  "project": %s,
  "resultsPath": "/root/xwikismoke/target/surefire-reports/"
}""" % (response2.text, response.text)
response3 = requests.post('http://localhost:37000/api/tjob', headers=headers, data=data)
print(response3.status_code)
print(response3.text)
print('####################################')


# We're good to go. Let's run the tjob.
import json
print("http://localhost:37000/api/tjob/%s/exec" % json.loads(response3.text)['id'])
response4 = requests.post("http://localhost:37000/api/tjob/%s/exec" % json.loads(response3.text)['id'], headers=headers, data="{}")
print(response4.status_code)
print(response4.text)
print('####################################')
