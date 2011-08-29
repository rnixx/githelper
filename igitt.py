#! /usr/bin/env python

import os
import sys
import urllib2
import json
import subprocess

def query_repos(context):
    url = 'http://github.com/api/v2/json/repos/show/%s' % context
    try:
        res = urllib2.urlopen(url)
    except urllib2.URLError, e:
        print e
        sys.exit(0)
    data = json.loads(res.read())
    res.close()
    return data

def print_usage_and_exit():
    print "Usage:"
    print "igitt clone context (package)"
    print "igitt pull (package)"
    sys.exit(0)

def perform_clone(context, package):
    base_uri = 'git@github.com:%s/%s.git'
    if package is not None:
        uri = base_uri % (context, package)
        cmd = ['git', 'clone', uri]
        subprocess.call(cmd)
        return
    
    data = query_repos(context)
    base_uri = 'git@github.com:%s/%s.git'
    for repo in data['repositories']:
        name = repo['name']
        uri = base_uri % (context, name)
        cmd = ['git', 'clone', uri]
        subprocess.call(cmd)

def perform_pull(package):
    if package is not None:
        os.chdir(package)
        # XXX: check for actual branch and define origin.
        cmd = ['git', 'pull']
        subprocess.call(cmd)
        return
    
    contents = os.listdir('.')
    for child in contents:
        if not os.path.isdir(child):
            continue
        os.chdir(child)
        if not '.git' in os.listdir('.'):
            os.chdir('..')
            continue
        # XXX: check for actual branch and define origin.
        cmd = ['git', 'pull']
        subprocess.call(cmd)
        os.chdir('..')

if __name__ == '__main__':
    args = sys.argv
    if len(args) < 2:
        print "No action specified. Aborting."
        print_usage_and_exit()
    
    action = args[1]
    if action not in ['clone', 'pull']:
        print "Invalid action '%s'" % action
        print_usage_and_exit()
    
    if action == 'clone':
        if len(args) < 3:
            print "No context specified. Aborting."
            print_usage_and_exit()
        context = args[2]
        package = None
        if len(args) > 3:
            package = args[3]
        perform_clone(context, package)
        sys.exit(0)
    
    if action == 'pull':
        package = None
        if len(args) > 2:
            package = args[2]
        perform_pull(package)
        sys.exit(0)
    
    print "Invalid action '%s'" % action
    print_usage_and_exit()