# Copyright 2011 Robert Lopez Toscano
#
# This file is part of Giterdone.
#
# Giterdone is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# Giterdone is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Giterdone. If not, see <http://www.gnu.org/licenses/>.

import logging
from re import sub
import os
import os.path
import subprocess

from giterdone.vcs.generic import GenericVcsInterface
import state

class GitInterface(GenericVcsInterface):

  _CLEAN_DRY_RUN_PREFIX = 'Would remove '
  _COMMIT_MSG_HEADER = '''

# To cancel this commit, close this file without making a change. To commit,
# write your message, then save and close the file.
#
'''
  _logger = logging.getLogger('giterdone.vcs.GitInterface')

  def __init__(self):
      super(GitInterface, self).__init__('git')

  def _add_ancestors(self, root_path, path, filemap, file_state):
    prev = filemap[path] if path in filemap else None
    # Overwrite file state based on precedence
    if (file_state == state.UNTRACKED) or \
       (file_state == state.DIRTY and prev != state.UNTRACKED) or \
       (file_state == state.STAGED and not prev in (state.UNTRACKED, state.DIRTY)) or \
       (file_state == state.SYNCED and not prev in (state.UNTRACKED, state.DIRTY, state.STAGED)) or \
       (file_state == state.IGNORED and not prev in (state.UNTRACKED, state.DIRTY, state.STAGED, state.SYNCED)):
      filemap[path] = file_state
    if (path + '/').startswith(root_path + '/'): # Recurse
      self._add_ancestors(root_path, os.path.dirname(path), filemap, file_state)

  def status(self, root_path):
    filemap = {} # file path -> vcs.state

    if not self.find_repo(root_path):
      raise RuntimeError('File not in a git repository: %s' % (root_path,))

    p = subprocess.Popen(['git', 'status', '--porcelain', '-uall'], cwd=root_path,
                         stdout=subprocess.PIPE)
    stdout, stderr = p.communicate()

    for line in stdout.split('\n'):
      if not line: continue
      path = os.path.join(root_path, line[3:])
      if line[:2] == '??':
        self._add_ancestors(root_path, path, filemap, state.UNTRACKED)
      elif line[1] != ' ':
        self._add_ancestors(root_path, path, filemap, state.DIRTY)
      elif line[1] == ' ':
        self._add_ancestors(root_path, path, filemap, state.STAGED)
      else:
        GitInterface._logger.warning(
            'Unexpected line in "git status --porcelain": "%s"', line)

    # The above git status --porcelain command gets me all the staged, dirty,
    # and untracked, but synced and ignored are still needed

    # find ignored files
    p = subprocess.Popen(['git', 'clean', '--dry-run', '-Xd'], cwd=root_path,
                         stdout=subprocess.PIPE)
    stdout, stderr = p.communicate()

    for line in stdout.split('\n'):
      if not line: continue
      if not line.startswith(GitInterface._CLEAN_DRY_RUN_PREFIX):
        GitInterface._logger.warning(
            'Unexpected line in "git clean --dry-run -Xd": "%s"', line)
        continue

      path = line[len(GitInterface._CLEAN_DRY_RUN_PREFIX):].strip('/')
      path = os.path.join(root_path, path)
      self._add_ancestors(root_path, path, filemap, state.IGNORED)

    # find synced files
    p = subprocess.Popen(['git', 'ls-files'], cwd=root_path,
                         stdout=subprocess.PIPE)
    stdout, stderr = p.communicate()

    for line in stdout.split('\n'):
      if not line: continue
      path = os.path.join(root_path, line)
      self._add_ancestors(root_path, path, filemap, state.SYNCED)

    return filemap

  def add(self, files):
    git_dir = self.find_repo(files[0])
    proc = subprocess.Popen(['git', 'add', '--'] + files, cwd=git_dir, stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()

  def checkout(self, paths):
    GitInterface._logger.info(
        'Performing "git checkout -- %s"' % (' '.join(paths),))
    git_dir = self.find_repo(paths[0])
    proc = subprocess.Popen(['git', 'checkout', '--'] + paths,
                            cwd=git_dir, stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()

  def reset(self, files):
    GitInterface._logger.info(
        'Performing "git reset -- %s"' % (' '.join(files),))
    git_dir = self.find_repo(files[0])
    proc = subprocess.Popen(['git', 'reset', '--'] + files,
                            cwd=git_dir, stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()

  def status_msg(self, git_dir, files=None):
    # HACK: Because 'git-status' has no '--no-color' option, we have check if coloring is enabled to
    # 'always', and remove color characters if so

    # Check if coloring is on
    possible_keys = ['color.ui', 'color.status', 'status.color']
    is_colored = False
    for k in possible_keys:
      proc = subprocess.Popen(['git', 'config', k], cwd=git_dir, stdout=subprocess.PIPE)
      stdout, stderr = proc.communicate()
      if stdout.startswith('always'):
          is_colored = True
          break

    if files == None:
      proc = subprocess.Popen(['git', 'status'], cwd=git_dir, stdout=subprocess.PIPE)
    else:
      proc = subprocess.Popen(['git', 'status', '--'] + files, cwd=git_dir, stdout=subprocess.PIPE)

    result, stderr = proc.communicate()

    # remove color characters if needed
    if is_colored: result = sub(r'\[\d*m', '', result)

    return result

  def commit(self, git_dir, commit_msg_path):
    proc = subprocess.Popen(
        ['git', 'commit', '--file='+commit_msg_path],
        cwd=git_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = proc.communicate()

  def commit_files(self, files, commit_msg_path):
    git_dir = self.find_repo(files[0])

    proc = subprocess.Popen(
        ['git', 'commit', '--file='+commit_msg_path, '--'] + files,
        cwd=git_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = proc.communicate()
    # TODO handle any error cases

  def fetch(self, git_dir):
    proc = subprocess.Popen(['git', 'fetch'], cwd=git_dir, stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    # TODO handle any error cases

  def find_repo(self, path):
    # iteratively check up the directories for a .git folder
    cur_dir = path
    while cur_dir != '/':
      if os.path.isdir(os.path.join(cur_dir,'.git')): return cur_dir
      cur_dir = os.path.dirname(cur_dir)
    return None

  def diff(self, paths):
    '''Assumes that all paths are in the same git repository'''
    git_dir = self.find_repo(paths[0])
    if not git_dir:
      raise RuntimeError('File not in a git repository: %s' % (paths[0],))
    subprocess.Popen(
            ['git', 'difftool', '--no-prompt'] + paths,
            cwd=git_dir, stdout=None, stderr=None, stdin=None)

  def has_msg(self, commit_msg):
    for line in commit_msg.split('\n'):
      line = line.strip(' \n')
      if line.startswith('#'): continue
      if line.startswith('no changes added to commit'): continue
      if line != '': return True
    return False

  def commit_msg_template(self, root_path, paths=None):
    return GitInterface._COMMIT_MSG_HEADER + self.status_msg(root_path, paths)

  def branch_name(self, root_path):
    p = subprocess.Popen(['git', 'branch'], cwd=root_path, stdout=subprocess.PIPE)
    stdout, stderr = p.communicate()
    for line in stdout.split('\n'):
      if line.startswith('*'):
        return line[2:]
    return None
