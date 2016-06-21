#!/usr/bin/python
import json
import subprocess;
from flask import Flask
import time
import os
import sqlite3
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

app = Flask(__name__);


#c.execute('''CREATE TABLE  Projects(name text)''')
#c.execute('''CREATE TABLE  ProjectServer(project text, server_id text)''')


# Insert a row of data
#c.execute("INSERT INTO stocks VALUES ('2006-01-05','BUY','RHAT',100,35.14)")



class DbAdapter():
	conn = sqlite3.connect('example.db',check_same_thread=False);
	c = conn.cursor();
	@staticmethod
	def addProjectIfNotPresent(name):
		isPresent = False;
		for row in DbAdapter.c.execute("SELECT name FROM Projects WHERE name = '%s'"%name):
			isPresent = True;
		return isPresent;
	@staticmethod
	def getIpOfProject(name):
		lista = [];
		for row in DbAdapter.c.execute("SELECT * FROM ProjectServer WHERE project = '%s'"%name):
			lista.append(row[1]);
		if lista:
			return lista[0]
		else:
			return None

	@staticmethod
	def terminateProject(name):
		DbAdapter.c.execute("DELETE FROM ProjectServer WHERE project = '%s'"%name);
		DbAdapter.c.execute("DELETE FROM Projects WHERE name = '%s'"%name);
		DbAdapter.conn.commit();

	@staticmethod
	def addInstance(name,i_id):
		pass
		DbAdapter.c.execute("INSERT INTO ProjectServer VALUES ('%(name)s','%(id)s')"%{"name":name,"id":i_id});
		DbAdapter.c.execute("INSERT INTO Projects VALUES ('%(name)s')"%{"name":name});

		DbAdapter.conn.commit();

class CloudAdapter():
	
	@staticmethod
	def launchInstance():
		data = subprocess.Popen(['aws','ec2','run-instances','--image-id','image id','--count','1','--instance-type','t2.micro','--key-name','key name','--security-group-ids','security group ids'], stdout=subprocess.PIPE).stdout.read();
		b = json.loads(data);
		return b["Instances"][0]["InstanceId"]
   

	ACCESS_ID = 'My Access Id'
	
	SECRET_KEY = 'My secret key'
	@staticmethod
	def start_node (node_id):
		cls = get_driver(Provider.EC2)
		driver = cls(CloudAdapter.ACCESS_ID, CloudAdapter.SECRET_KEY, region="us-west-2")
		nodes = driver.list_nodes()
		#print nodes        
		inst = [i for i in nodes if i.id == node_id][0]
		print inst
		done = driver.ex_start_node(inst)
		return done

	@staticmethod
	def stop_node(node_id):
		cls = get_driver(Provider.EC2)
		driver = cls(CloudAdapter.ACCESS_ID, CloudAdapter.SECRET_KEY, region="us-west-2")
		nodes = driver.list_nodes()        
		inst = [i for i in nodes if i.id == node_id][0]
		done = driver.ex_stop_node(inst)
		return done

	@staticmethod
	def terminate_node(node_id):
		cls = get_driver(Provider.EC2)
		driver = cls(CloudAdapter.ACCESS_ID, CloudAdapter.SECRET_KEY, region="us-west-2")
		nodes = driver.list_nodes()        
		inst = [i for i in nodes if i.id == node_id][0]
		done = driver.destroy_node(inst)
		return done
	@staticmethod
	def status_node(node_id):
		cls = get_driver(Provider.EC2)
		driver = cls(CloudAdapter.ACCESS_ID, CloudAdapter.SECRET_KEY, region="us-west-2")
		nodes = driver.list_nodes()        
		done = [i.state for i in nodes if i.id == node_id][0]
		return done
	
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
	def upload_server_ansible(ip,proj,fileName):
		print "war file is "+ fileName +" proj is "+ proj;
		AnsibleAdapter.add_ip(ip);
		#subprocess.Popen(['ssh-add','/home/mostafa/mostafa.pem'])
		data=subprocess.Popen(['ansible-playbook','--extra-vars' ,'{"file":"%(file)s","project":%(proj)s}'%{"file":fileName,"proj":proj},'-l',ip,'site.yml'], stdout=subprocess.PIPE)
		#data.stdin.write('yes');
		#print data.communicate()[0]
		#data.stdin.close()
		return data.stdout.read();

@app.route("/")
def index():
	return 'this is the homepage'

#@app.route("/meat")
#def tuna():
#	return "<h2>good meat</h2>"





#@app.route("/hi/<user>")
#def hi(user):
#	return "hi "+user;
import re

@app.route("/geturl/<gitName>")
def getUrl(gitName):
	return CloudAdapter.getIpFromId(DbAdapter.getIpOfProject(gitName))

@app.route("/subscribe/<gitName>/<repoName>")
def subscribe(gitName,repoName):
	i_id = None;
	if DbAdapter.addProjectIfNotPresent(gitName):
		i_id = DbAdapter.getIpOfProject(gitName);
	else:
		i_id = CloudAdapter.launchInstance();
		DbAdapter.addInstance(gitName,i_id);
	while True:
		ip = CloudAdapter.getIpFromId(i_id);
		if ip:
			break;

	while not CloudAdapter.check_server(ip):
		pass;

	time.sleep(5);
	repoName = re.sub("-","/", repoName)	

	print AnsibleAdapter.upload_server_ansible(ip,gitName,repoName);
	return ip	 	


@app.route("/stop/<projectname>")
def stop(projectname):
	i_id = None;
	if DbAdapter.addProjectIfNotPresent(projectname):
		i_id = DbAdapter.getIpOfProject(projectname);
		done = CloudAdapter.stop_node(i_id)
		if done:
			return "True"

	return "False"

@app.route("/terminate/<projectname>")
def terminate(projectname):
	i_id = None;
	if DbAdapter.addProjectIfNotPresent(projectname):
		i_id = DbAdapter.getIpOfProject(projectname);
		print i_id
		done = CloudAdapter.terminate_node(i_id)
		DbAdapter.terminateProject(projectname);
		if done:
			return "True"

	return "False"


@app.route("/start/<projectname>")
def start(projectname):
	i_id = None;
	if DbAdapter.addProjectIfNotPresent(projectname):
		i_id = DbAdapter.getIpOfProject(projectname);
		if CloudAdapter.status_node(i_id) != 0:
			done = CloudAdapter.start_node(i_id)
			if done:
				return "True"

	return "False"
	
@app.route("/status/<projectname>")
def status(projectname):
	print "uuuuuu "+projectname
	i_id = None;
	if DbAdapter.addProjectIfNotPresent(projectname):
		i_id = DbAdapter.getIpOfProject(projectname);
		print i_id
		done = CloudAdapter.status_node(i_id)
		print done
		return str(done)
		 	

if __name__ == "__main__" and True: 
	app.run(debug=True,port=6666);



#print CloudAdapter.launchInstance()

#ec2-52-10-52-219.us-west-2.compute.amazonaws.com

#print CloudAdapter.check_server("ec2-52-27-173-70.us-west-2.compute.amazonaws.com")
#i_id = DbAdapter.getIpOfProject('TamerB_CounterWebApp');
# DbAdapter.c.execute("DELETE from Projects")
# DbAdapter.c.execute("DELETE From ProjectServer")
# DbAdapter.conn.commit();
# # print i_id

# # print CloudAdapter.status_node(i_id)
# for row in DbAdapter.c.execute("SELECT * From Projects"):
# 	print  row
# for row in DbAdapter.c.execute("SELECT * From ProjectServer"):
# 	print  row
