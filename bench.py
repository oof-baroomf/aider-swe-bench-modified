#!/usr/bin/env python

import os
import sys

from pathlib import Path
from collections import defaultdict

from datasets import load_dataset

from dump import dump

REPOS_DNAME = 'repos'

import subprocess


def files_in_patch(patch):
    """
    Extract the list of modified files from a unified diff patch string.
    """
    files = []
    for line in patch.split('\n'):
        if line.startswith('--- a/') or line.startswith('+++ b/'):
            fname = line.split('/', 1)[1]
            if fname not in files:
                files.append(fname)
    return files

def clone_repo(url, dname):
    """
    Clone the repository from the given URL into the specified directory.
    """
    cmd = f"git clone {url} {dname}"
    subprocess.run(cmd.split(), check=True)

def checkout_commit(dname, commit):
    """
    Checkout the specified commit in the given directory.
    """
    cmd = f"git -C {dname} checkout {commit}"
    subprocess.run(cmd.split(), check=True)

def checkout_repo(url, commit):
    # Extract repo name from URL
    repo_name = url.split("/")[-1].split(".")[0]

    # Create directory path for repo
    repo_dir = Path(REPOS_DNAME) / repo_name

    # If repo directory doesn't exist, clone the repo
    if not repo_dir.exists():
        clone_repo(url, repo_dir)

    # Checkout the specified commit
    checkout_commit(repo_dir, commit)

    return repo_dir


dataset = load_dataset("princeton-nlp/SWE-bench_Lite")

instance_id = 'django__django-12983'

for entry in dataset['test']:
    if entry['instance_id'] == instance_id:
        break
    #print(entry['instance_id'])

print("-" * 40)  # Separator between entries
for attribute, value in entry.items():
    print(f"{attribute}")#: {value}")

github_url = 'https://github.com/'
repo_url = github_url + entry['repo']
commit = entry['base_commit']

git_dname = checkout_repo(repo_url, commit)

gold_patch = entry['patch']

gold_files = files_in_patch(gold_patch)


from aider.coders import Coder
from aider.models import Model
from aider import utils

model = Model("deepseek/deepseek-chat")

os.chdir(git_dname)

# Create a coder object
coder = Coder.create(
    main_model=model,
    fnames=gold_files,
    git_dname=git_dname,
)

#dump(coder.abs_fnames)
#messages = coder.format_messages()
#utils.show_messages(messages)

problem = entry["problem_statement"]
coder.run(problem)


# TODO: do a git diff between the current repo state and `commit`
