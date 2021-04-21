#! /usr/bin/env python

"""
Simple helper script for working on multiple git repositories in a
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

For showing repository diff, use:
    igitt diff [PACKAGE]

For committing all repository changes, use:
    igitt cia 'MESSAGE' [PACKAGE]

For pushing all committed changes, use:
    igitt push [PACKAGE]

For discarding all changes, use:
    igitt co [package]


Install
-------

Checkout this script and create a symlink in '/usr/local/bin'.

This script requires python2.7 or python2.6 with 'argparse' package installed
"""

from __future__ import print_function
from argparse import ArgumentParser

import json
import os
import subprocess
import sys
import six.moves.urllib.request, six.moves.urllib.error, six.moves.urllib.parse


mainparser = ArgumentParser(description="Git helper utilities")
subparsers = mainparser.add_subparsers(help="commands")


def hilite(string, color, bold):
    # http://stackoverflow.com/questions/5947742/how-to-change-the-output-color-of-echo-in-linux
    # http://stackoverflow.com/questions/2330245/python-change-text-color-in-shell
    attr = []
    if color == "green":
        attr.append("32")
    elif color == "red":
        attr.append("31")
    elif color == "blue":
        attr.append("34")
    if bold:
        attr.append("1")
    return "\x1b[%sm%s\x1b[0m" % (";".join(attr), string)


def query_repos(context):
    org_url = "https://api.github.com/orgs/%s/repos" % context
    user_url = "https://api.github.com/users/%s/repos" % context
    query = "%s?page=%i&per_page=50"
    data = list()
    page = 1
    while True:
        try:
            url = query % (org_url, page)
            res = six.moves.urllib.request.urlopen(url)
        except six.moves.urllib.error.URLError as e:
            try:
                url = query % (user_url, page)
                res = six.moves.urllib.request.urlopen(url)
            except six.moves.urllib.error.URLError as e:
                print(e)
                sys.exit(0)
        page_data = json.loads(res.read())
        res.close()
        if not page_data:
            break
        data += page_data
        page += 1
    print("Fetched %i repositories for '%s'" % (len(data), context))
    return data


def perform_clone(arguments):
    base_uri = "git@github.com:%s/%s.git"
    context = arguments.context[0]
    if arguments.repository:
        repos = arguments.repository
    else:
        repos = [_["name"] for _ in query_repos(args.context)]
    for repo in repos:
        uri = base_uri % (context, repo)
        cmd = ["git", "clone", uri]
        subprocess.call(cmd)


sub = subparsers.add_parser("clone", help="Clone from an organisation or a user")
sub.add_argument("context", nargs=1, help="Name of organisation or user")
sub.add_argument(
    "repository",
    nargs="*",
    help="Name of repositories to clone, leave empty to clone all",
)
sub.set_defaults(func=perform_clone)


def get_branch():
    cmd = "git branch"
    p = subprocess.Popen(
        cmd,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
    )
    output = p.stdout.readlines()
    for line in output:
        line = line.decode("utf-8")  # python3 returns bytes, python2 doesn't break.
        if line.strip().startswith("*"):
            return line.strip().strip("*").strip()


def perform_pull(arguments):
    if arguments.repository:
        dirnames = arguments.repository
    else:
        dirnames = os.listdir(".")
    for child in dirnames:
        if not os.path.isdir(child):
            continue
        if ".git" not in os.listdir(child):
            continue
        os.chdir(child)
        print("Perform pull for '%s'" % hilite(child, "blue", True))
        cmd = ["git", "pull", "origin", get_branch()]
        subprocess.call(cmd)
        os.chdir("..")


sub = subparsers.add_parser("pull", help="Pull distinct or all repositories in folder.")
sub.add_argument(
    "repository",
    nargs="*",
    help="Name of repositories to pull, leave empty to pull all",
)
sub.set_defaults(func=perform_pull)


def perform(cmd):
    pr = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = pr.communicate()
    print(stdout)
    if pr.returncode != 0:
        print("%s failed to perform: exit code %s" % (" ".join(cmd), pr.returncode))
        print(stderr)


def perform_backup(arguments):
    context = arguments.context[0]
    if context not in os.listdir("."):
        os.mkdir(context)
    os.chdir(context)
    contents = os.listdir(".")
    data = query_repos(context)
    base_uri = "git@github.com:%s/%s.git"
    for repo in data:
        name = repo["name"]
        fs_name = "%s.git" % name
        if fs_name in contents:
            print("Fetching existing local repository '%s'" % fs_name)
            os.chdir(fs_name)
            perform(["git", "fetch", "origin"])
            os.chdir("..")
        else:
            print("Cloning new repository '%s'" % fs_name)
            uri = base_uri % (context, name)
            perform(["git", "clone", "--bare", "--mirror", uri])


sub = subparsers.add_parser(
    "backup", help="Backup all repositories from an organisation or a user"
)
sub.add_argument("context", nargs=1, help="Name of organisation or user")
sub.set_defaults(func=perform_backup)


def perform_status(arguments):
    if arguments.repository:
        dirnames = arguments.repository
    else:
        dirnames = os.listdir(".")
    for child in dirnames:
        if not os.path.isdir(child):
            continue
        if ".git" not in os.listdir(child):
            continue
        os.chdir(child)
        print("Status for '%s'" % hilite(child, "blue", True))
        cmd = ["git", "status"]
        subprocess.call(cmd)
        os.chdir("..")


sub = subparsers.add_parser(
    "st", help="Status of distinct or all repositories in current folder."
)
sub.add_argument(
    "repository",
    nargs="*",
    help="Name of repositories to show, leave empty to show all",
)
sub.set_defaults(func=perform_status)


def perform_b(arguments):
    if arguments.repository:
        dirnames = arguments.repository
    else:
        dirnames = os.listdir(".")
    for child in dirnames:
        if not os.path.isdir(child):
            continue
        if ".git" not in os.listdir(child):
            continue
        os.chdir(child)
        print("Branches for '%s'" % hilite(child, "blue", True))
        cmd = ["git", "branch"]
        subprocess.call(cmd)
        os.chdir("..")


sub = subparsers.add_parser(
    "b", help="Show branches of distinct or all repositories in current folder."
)
sub.add_argument(
    "repository",
    nargs="*",
    help="Name of repositories to show, leave empty to show all",
)
sub.set_defaults(func=perform_b)


def perform_diff(arguments):
    if arguments.repository:
        dirnames = arguments.repository
    else:
        dirnames = os.listdir(".")
    for child in dirnames:
        if not os.path.isdir(child):
            continue
        if ".git" not in os.listdir(child):
            continue
        os.chdir(child)
        print("Diff for '%s'" % hilite(child, "blue", True))
        cmd = ["git", "diff"]
        subprocess.call(cmd)
        os.chdir("..")


sub = subparsers.add_parser(
    "diff", help="Show diff of distinct or all repositories in current folder."
)
sub.add_argument(
    "repository",
    nargs="*",
    help="Name of repositories to show diff of, leave empty to show all",
)
sub.set_defaults(func=perform_diff)


def perform_cia(arguments):
    if arguments.repository:
        dirnames = arguments.repository
    else:
        dirnames = os.listdir(".")
    message = '"' + arguments.message[0] + '"'
    for child in dirnames:
        if not os.path.isdir(child):
            continue
        if ".git" not in os.listdir(child):
            continue
        os.chdir(child)
        print("Commit all changes resources for '%s'" % hilite(child, "blue", True))
        cmd = ["git", "cia", "-m", message]
        subprocess.call(cmd)
        os.chdir("..")


sub = subparsers.add_parser(
    "cia",
    help="Commit all changes of distinct or all repositories in current " "folder.",
)
sub.add_argument("message", nargs=1, help="Commit message")
sub.add_argument(
    "repository",
    nargs="*",
    help="Name of repositories to commit, leave empty to commit all",
)
sub.set_defaults(func=perform_cia)


def perform_push(arguments):
    if arguments.repository:
        dirnames = arguments.repository
    else:
        dirnames = os.listdir(".")
    for child in dirnames:
        if not os.path.isdir(child):
            continue
        if ".git" not in os.listdir(child):
            continue
        os.chdir(child)
        print("Perform push for '%s'" % hilite(child, "blue", True))
        cmd = ["git", "push", "origin", get_branch()]
        subprocess.call(cmd)
        os.chdir("..")


sub = subparsers.add_parser("push", help="Push distinct or all repositories in folder.")
sub.add_argument(
    "repository",
    nargs="*",
    help="Name of repositories to push, leave empty to push all",
)
sub.set_defaults(func=perform_push)


def perform_co(arguments):
    if arguments.repository:
        dirnames = arguments.repository
    else:
        dirnames = os.listdir(".")
    for child in dirnames:
        if not os.path.isdir(child):
            continue
        if ".git" not in os.listdir(child):
            continue
        os.chdir(child)
        print("Perform checkout for '%s'" % hilite(child, "blue", True))
        cmd = ["git", "checkout", "."]
        subprocess.call(cmd)
        os.chdir("..")


sub = subparsers.add_parser("co", help="Discard all uncommited changes.")
sub.add_argument(
    "repository",
    nargs="*",
    help="Name of repositories to discard, leave empty to discard all",
)
sub.set_defaults(func=perform_co)


if __name__ == "__main__":
    args = mainparser.parse_args()
    args.func(args)
