#! /usr/bin/env python

"""
Simple helper script for cloning and pulling multiple git repositories in a
specific directory.

This script is useful if you work with 'mr.developer' sources for project
development or if you want to perform backups of a github account.

Usage
-----

For cloning repositories, use:
    igitt clone CONTEXT [PACKAGE]

For updating repositories, use:
    igitt pull [PACKAGE]

For backup of context, use:
    igitt backup CONTEXT

For checking repository state, use:
    igitt st [PACKAGE]

For listing repository branch, use:
    igitt b [PACKAGE]

Install
-------

Checkout this script and create a symlink in '/usr/local/bin'.
"""

import os
import sys
import urllib2
import json
import subprocess


def query_repos(context):
    org_url = 'https://api.github.com/orgs/%s/repos' % context
    user_url = 'https://api.github.com/users/%s/repos' % context
    query = '%s?page=%i&per_page=50'
    data = list()
    page = 1
    while True:
        try:
            url = query % (org_url, page)
            res = urllib2.urlopen(url)
        except urllib2.URLError, e:
            try:
                url = query % (user_url, page)
                res = urllib2.urlopen(url)
            except urllib2.URLError, e:
                print e
                sys.exit(0)
        page_data = json.loads(res.read())
        res.close()
        if not page_data:
            break
        data += page_data
        page += 1
    print "Fetched %i reposirories for '%s'" % (len(data), context)
    return data


def print_usage_and_exit():
    print "Usage:"
    print "For cloning repositories, use:"
    print "    igitt clone CONTEXT [PACKAGE]"
    print "For updating repositories, use:"
    print "    igitt pull [PACKAGE]"
    print "For backup of context, use:"
    print "    igitt backup CONTEXT"
    print "For checking repository state, use:"
    print "    igitt st [PACKAGE]"
    print "For listing repository branch, use:"
    print "    igitt b [PACKAGE]"
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
    for repo in data:
        name = repo['name']
        uri = base_uri % (context, name)
        cmd = ['git', 'clone', uri]
        subprocess.call(cmd)


def get_branch():
    cmd = 'git branch'
    p = subprocess.Popen(
        cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, close_fds=True)
    output = p.stdout.readlines()
    for line in output:
        if line.strip().startswith('*'):
            return line.strip().strip('*').strip()


def perform_pull(package):
    if package is not None:
        print "Perform pull for '%s'" % package
        os.chdir(package)
        branch = get_branch()
        cmd = ['git', 'pull', 'origin', branch]
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
        print "Perform pull for '%s'" % child
        branch = get_branch()
        cmd = ['git', 'pull', 'origin', branch]
        subprocess.call(cmd)
        os.chdir('..')


def perform_backup(context):
    if not context in os.listdir('.'):
        os.mkdir(context)
    os.chdir(context)
    contents = os.listdir('.')
    data = query_repos(context)
    base_uri = 'git@github.com:%s/%s.git'
    for repo in data:
        name = repo['name']
        fs_name = '%s.git' % name
        if fs_name in contents:
            print "Fetching existing local repository '%s'" % fs_name
            os.chdir(fs_name)
            cmd = ['git', 'fetch', 'origin']
            subprocess.call(cmd)
            os.chdir('..')
        else:
            print "Cloning new repository '%s'" % fs_name
            uri = base_uri % (context, name)
            cmd = ['git', 'clone', '--bare', '--mirror', uri]
            subprocess.call(cmd)


def perform_st(package):
    if package is not None:
        print "Status for '%s'" % package
        os.chdir(package)
        cmd = ['git', 'status']
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
        print "Status for '%s'" % child
        cmd = ['git', 'status']
        subprocess.call(cmd)
        os.chdir('..')


def perform_b(package):
    if package is not None:
        print "Branches for '%s'" % package
        os.chdir(package)
        cmd = ['git', 'branch']
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
        print "Branches for '%s'" % child
        cmd = ['git', 'branch']
        subprocess.call(cmd)
        os.chdir('..')


if __name__ == '__main__':
    args = sys.argv
    if len(args) < 2:
        print "No action specified. Aborting."
        print_usage_and_exit()
    
    action = args[1]
    if action not in ['clone', 'pull', 'backup', 'st', 'b']:
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
    
    if action == 'backup':
        if len(args) != 3:
            print "Need context to perform backup"
            print_usage_and_exit()
        context = args[2]
        perform_backup(context)
        sys.exit(0)
    
    if action == 'st':
        package = None
        if len(args) > 2:
            package = args[2]
        perform_st(package)
        sys.exit(0)
    
    if action == 'b':
        package = None
        if len(args) > 2:
            package = args[2]
        perform_b(package)
        sys.exit(0)
    
    print "Invalid action '%s'" % action
    print_usage_and_exit()