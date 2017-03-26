#!/usr/bin/env python  
#coding=utf-8
#  
# Generate a list of dnsmasq rules with ipset for gfwlist
#  
# Copyright (C) 2014 http://www.shuyz.com   
# Ref https://code.google.com/p/autoproxy-gfwlist/wiki/Rules    
 
import urllib2 
import re
import os
import datetime
import base64
import shutil

import ssl
 

mydnsip = '127.0.0.1'
mydnsport = '5300'

def write_rules(comment,input_file_path,output_rule_name):
	comment_pattern = '^\!|\[|^@@|^\d+\.\d+\.\d+\.\d+'
	domain_pattern = '([\w\-\_]+\.[\w\.\-\_]+)[\/\*]*' 
	
	temp_output_rule_path = '/tmp/' + output_rule_name;
	output_rule_path = '/etc/dnsmasq.d/' + output_rule_name;

	try:
		input_file = open(input_file_path, 'r')
		temp_output_file = open(temp_output_rule_path,'w')
	except:
		return

	temp_output_file.write('# '+comment+'\n')
	temp_output_file.write('# updated on ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '\n')
	temp_output_file.write('#\n')
	
	domainlist = []
	for line in input_file.readlines():	
		if re.findall(comment_pattern, line):
			print 'this is a comment line: ' + line
		else:
			domain = re.findall(domain_pattern, line)
			if domain:
				try:
					found = domainlist.index(domain[0])
					print domain[0] + ' exists.'
				except ValueError:
					print 'saving ' + domain[0]
					domainlist.append(domain[0])
					temp_output_file.write('server=/.%s/%s#%s\n'%(domain[0],mydnsip,mydnsport))
					#temp_output_file.write('ipset=/.%s/gfwlist\n'%domain[0])
			else:
				print 'no valid domain in this line: ' + line

	temp_output_file.close()	
	input_file.close();

	print 'moving generated file to dnsmasg directory'
	shutil.move(temp_output_rule_path, output_rule_path)
	return
 
def download_gfw_list(download_path):
	baseurl = 'https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt'
	print 'fetching list...'
	context = ssl._create_unverified_context()
	content = urllib2.urlopen(baseurl, timeout=15,context=context).read().decode('base64')
	gfw_tmp = open(download_path, 'w')
	gfw_tmp.write(content)
	gfw_tmp.close()

tmpfile = '/tmp/gfwlisttmp'
download_gfw_list(tmpfile)

print 'page content fetched, analysis...'

write_rules('gfw list ipset rules for dnsmasq',tmpfile,'gfwlist.conf')
write_rules('custom list rules for dnsmasq','custom.list','custom.conf')

print 'restart dnsmasq...'
print os.popen('/etc/init.d/dnsmasq restart').read()
 
print 'done!'