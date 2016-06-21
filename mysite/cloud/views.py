from django.shortcuts import render

# Create your views here.
import json
import subprocess;
import time
import os



class CloudAdapter():
	
	@staticmethod
	def launchInstance():
		data = subprocess.Popen(['aws','ec2','run-instances','--image-id','image id','--count','1','--instance-type','t2.micro','--key-name','mostafa','--security-group-ids','security group ids'], stdout=subprocess.PIPE).stdout.read();
		b = json.loads(data);
		return b["Instances"][0]["InstanceId"]

	
	@staticmethod
	def getIpFromId(i_id):
		data = subprocess.Popen(['aws','ec2','describe-instances','--query','Reservations[*].Instances[*].[InstanceId,PublicDnsName]'], stdout=subprocess.PIPE).stdout.read();
		data = json.loads(data);#subprocess.Popen(['grep '+ i_id],stdin=data,stdout=subprocess.PIPE).stdout.read(); 
		
		for elem in data:
			if str(elem[0][0]) == i_id:
				return elem[0][1]
		return None
	@staticmethod
	def check_server(ip):
		return os.system("ping -c 1 " + ip) == 0;


class AnsibleAdapter():

	@staticmethod
	def add_ip(ip):
		with open('/etc/ansible/hosts', 'a') as file:
			file.write(ip+"\n");

	@staticmethod
	def execute_ansible(ip):
		AnsibleAdapter.add_ip(ip);
		#subprocess.Popen(['ssh-add','/home/mostafa/mostafa.pem'])
		
		data=subprocess.Popen(['ansible' ,'-u' ,'ubuntu' ,'-m', 'ping',ip], stdout=subprocess.PIPE)
		#data.stdin.write('yes');
		#print data.communicate()[0]
		#data.stdin.close()
		return data.stdout.read();

	@staticmethod
	def upload_server_ansible(ip):
		AnsibleAdapter.add_ip(ip);
		#subprocess.Popen(['ssh-add','/home/mostafa/mostafa.pem'])
		data=subprocess.Popen(['ansible-playbook' ,'-l',ip,'site.yml'], stdout=subprocess.PIPE)
		#data.stdin.write('yes');
		#print data.communicate()[0]
		#data.stdin.close()
		return data.stdout.read();

