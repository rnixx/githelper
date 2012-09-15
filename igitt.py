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
from argparse import ArgumentParser

mainparser = ArgumentParser(description='git helper utilities')
subparsers = mainparser.add_subparsers(help='commands')


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


def perform_clone(arguments):
    base_uri = 'git@github.com:%s/%s.git'
    context = arguments.context[0]
    if arguments.repository:
        repos = arguments.repository
    else:
        repos = [_['name'] for _ in query_repos(args.context)]
    for repo in repos:
        uri = base_uri % (context, repo)
        cmd = ['git', 'clone', uri]
        subprocess.call(cmd)

sub = subparsers.add_parser('clone',
                            help='Clone from an organisation or a user')
sub.add_argument('context', nargs=1, help='name of organisation or user')
sub.add_argument('repository', nargs='*',
                 help='name of repositories to fetch, leave empty to fetch all')
sub.set_defaults(func=perform_clone)


def get_branch():
    cmd = 'git branch'
    p = subprocess.Popen(
        cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, close_fds=True)
    output = p.stdout.readlines()
    for line in output:
        if line.strip().startswith('*'):
            return line.strip().strip('*').strip()


def perform_pull(arguments):
    if arguments.repository:
        dirnames = arguments.repository
    else:
        dirnames = os.listdir('.')

    for child in dirnames:
        if not os.path.isdir(child):
            continue
        if not '.git' in os.listdir(child):
            continue
        os.chdir(child)
        print "Perform pull for '%s'" % child
        cmd = ['git', 'pull', 'origin', get_branch()]
        subprocess.call(cmd)
        os.chdir('..')

sub = subparsers.add_parser('pull',
                            help='Pull distinct or all repositories in  folder.')
sub.add_argument('repository', nargs='*',
                 help='name of repositories to fetch, leave empty to fetch all')
sub.set_defaults(func=perform_pull)


def perform_backup(arguments):
    context = arguments.context[0]
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

sub = subparsers.add_parser('backup',
                            help='Backup all repositories from an organisation '
                                 'or a user')
sub.add_argument('context', nargs=1, help='name of organisation or user')
sub.set_defaults(func=perform_backup)


def perform_status(arguments):
    if arguments.repository:
        dirnames = arguments.repository
    else:
        dirnames = os.listdir('.')

    for child in dirnames:
        if not os.path.isdir(child):
            continue
        if not '.git' in os.listdir(child):
            continue
        os.chdir(child)
        print "Status for '%s'" % child
        cmd = ['git', 'status']
        subprocess.call(cmd)
        os.chdir('..')

sub = subparsers.add_parser('st',
                            help='Status of distinct or all repositories in '
                                 'current folder.')
sub.add_argument('repository', nargs='*',
                 help='name of repositories to check, leave empty to check all')
sub.set_defaults(func=perform_status)


def perform_b(arguments):
    if arguments.repository:
        dirnames = arguments.repository
    else:
        dirnames = os.listdir('.')

    for child in dirnames:
        if not os.path.isdir(child):
            continue
        if not '.git' in os.listdir(child):
            continue
        os.chdir(child)
        print "Branches for '%s'" % child
        cmd = ['git', 'branch']
        subprocess.call(cmd)
        os.chdir('..')


sub = subparsers.add_parser('b',
                            help='Show branches of distinct or all '
                                 'repositories in current folder.')
sub.add_argument('repository', nargs='*',
                 help='name of repositories to show, leave empty to show all')
sub.set_defaults(func=perform_b)

if __name__ == '__main__':
    args = mainparser.parse_args()
    args.func(args)
