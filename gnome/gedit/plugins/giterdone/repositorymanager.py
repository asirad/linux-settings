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
import os.path

from giterdone.repository import Repository
import giterdone.vcs as vcs
import giterdone.vcs.state as state

class RepositoryManager(object):
  _logger = logging.getLogger('giterdone.RepositoryManager')

  def __init__(self, repo_monitor):
    self._repo_monitor = repo_monitor

  def in_same_repo(self, paths):
    return self._find_common_repo(paths) != None

  def any_are_dirty(self, paths):
    """Assumes all paths in 'paths' belong to the same repository"""
    repo = self._find_common_repo(paths)
    for path in paths:
      file_state = self._repo_monitor._get_file_state(repo.path, path)
      if file_state == state.DIRTY: return True
    else:
      return False

  def any_are_untracked_or_dirty(self, paths):
    repo = self._find_common_repo(paths)
    for path in paths:
      file_state = self._repo_monitor._get_file_state(repo.path, path)
      if file_state == state.UNTRACKED or file_state == state.DIRTY:
        return True
    else:
      return False

  def any_are_staged(self, paths):
    repo = self._find_common_repo(paths)
    for path in paths:
      file_state = self._repo_monitor._get_file_state(repo.path, path)
      if file_state == state.STAGED: return True
    else:
      return False

  def all_are_synced(self, paths):
    repo = self._find_common_repo(paths)
    for path in paths:
      file_state = self._repo_monitor._get_file_state(repo.path, path)
      if file_state != state.SYNCED:
        return False
    else:
      return True

  def reset(self, paths):
    repo = self._find_common_repo(paths)
    if not repo:
      RepositoryManager._logger.warning(
          'Aborting vcs-reset: at least one selected file is not under vcs, ' \
          'or not all selected files under same repository')
      return
    vcs.interfaces[repo.type].reset(paths)
    self._repo_monitor.update_files(paths)

  def add(self, paths):
    repo = self._find_common_repo(paths)
    if not repo:
      RepositoryManager._logger.warning(
          'Aborting vcs-add: at least one selected file is not under vcs, or ' \
          'not all selected files under same repository')
      return
    vcs.interfaces[repo.type].add(paths)
    RepositoryManager._logger.info('Paths added to vcs: '+str(paths))
    self._repo_monitor.update_files(paths)

  def diff(self, paths):
    repo = self._find_common_repo(paths)
    if not repo:
      RepositoryManager._logger.warning(
          'Aborting vcs-diff: at least one selected file is not under vcs, ' \
          'or not all selected files under same repository.')
      return
    vcs.interfaces[repo.type].diff(paths)

  def checkout(self, paths):
    repo = self._find_common_repo(paths)
    if not repo:
      RepositoryManager._logger.warning(
          'Aborting vcs-checkout: at least one selected file is not under ' \
          'vcs, or not all selected files under same repository.')
      return
    vcs.interfaces[repo.type].checkout(paths)
    self._repo_monitor.update_files(paths)

  def commit(self, paths):
    repo = self._find_common_repo(paths)
    if not repo:
      RepositoryManager._logger.warning(
          'Aborting vcs-commit: at least one selected file is not under vcs, ' \
          'or not all selected files under same repository.')
      return
    vcs.interfaces[repo.type].commit(paths)
    self._repo_monitor.update_files(paths)

  def get_commit_msg_template(self, paths):
    repo = self._find_common_repo(paths)
    if not repo:
      RepositoryManager._logger.warning(
          'Aborting vcs-commit-msg-template: at least one selected file is ' \
          'not under vcs, or not all selected files under same repository.')
      return None
    return vcs.interfaces[repo.type].commit_msg_template(repo.path, paths)

  def commit_files(self, paths, commit_msg_path):
    repo = self._find_common_repo(paths)
    if not repo:
      RepositoryManager._logger.warning(
          'Aborting vcs-commit-msg-template: at least one selected file is ' \
          'not under vcs, or not all selected files under same repository.')
      return
    # check if commit_msg had any text in it
    f = open(commit_msg_path, 'r')
    commit_msg = f.read()
    f.close()

    if vcs.interfaces[repo.type].has_msg(commit_msg):
      # Check if doing root-level commit, otherwise commit individual files.
      if len(paths) == 1 and paths[0] == repo.path:
        vcs.interfaces[repo.type].commit(repo.path, commit_msg_path)
      else:
        vcs.interfaces[repo.type].commit_files(paths, commit_msg_path)
      self._repo_monitor.update_files(paths)

  def _find_common_repo(self, paths):
    for vcs_type, vcs_interface in vcs.interfaces.iteritems():
      repo_path = vcs_interface.find_repo(paths[0])
      if repo_path:
        # Verify all paths are in this repository
        for path in paths[1:]:
          if not (path + '/').startswith(repo_path + '/'): return None
        return Repository(vcs_type, repo_path)
    return None
