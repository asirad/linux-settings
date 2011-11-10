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

import os.path

import gobject

from giterdone.repository import Repository
import giterdone.vcs as vcs

class RepositoryMonitor(object):
  """Maintains the VCS state of all the files which it is instructed to monitor
  as well as their associated repositories.

  A user monitors file paths via the update_file function and stops monitoring
  them via the remove_file function.  The repository monitor infers which
  repositories to monitor by getting the paths each of the repositories that the
  monitored files belong to.

  All paths passed into or returned from the repository monitor's functions must
  be absolute file paths.

  The repository monitor will fire subscribable events that indicate when a
  file's or repository's VCS state has changed. Use the subscribe and
  unsubscribe functions to listen for these events.
  """

  def __init__(self):
    """Creates a repository monitor that initially monitors no files."""
    self._repos = set() # All monitored repositories
    self._file_state_subscribers = [] # Callbacks for file VCS state changes
    self._repo_discovery_subscribers = []
    self._repo_branch_subscribers = []
    self._repo_state_subscribers = []
    self._is_running = False
    self._files_to_update = {} # repo -> list(file paths)
    self._repos_to_update = set()

  def update_files(self, paths):
    for path in paths: self.update_file(path)

  def update_file(self, path):
    """Schedule the file's VCS state to be updated.

    Returns:
      True if the path is under a VCS, False otherwise.
    """
    # Check if we already monitor this file's repo
    for repo in self._repos:
      if path.startswith(repo.path+'/') or path == repo.path:
        self._monitor_file_and_dependants(repo, path)
        return True

    # Otherwise find its repo path and update repository monitor
    for interface in vcs.interfaces.values():
      repo_path = interface.find_repo(path)
      if repo_path:
        repo = Repository(interface.type, repo_path)
        self._repos.add(repo)
        for callback in self._repo_discovery_subscribers: callback(repo)
        self._monitor_file_and_dependants(repo, path)
        return True

    return False

  def remove_file(self, path):
    pass

  def subscribe_to_file_changes(self, callback):
    """Registers a callback to be invoked when a file's VCS state has changed.

    Arguments:
      callback <function(string, giterdone.vcs.state)> The first argument of the
          callback is the absolute file path of the file that has changed.  The
          second argument is the file's new VCS state.
    """
    self._file_state_subscribers.append(callback)

  def unsubscribe_to_file_changes(self, callback):
    self._file_state_subscribers.remove(callback)

  def subscribe_to_repo_discoveries(self, callback):
    self._repo_discovery_subscribers.append(callback)

  def unsubscribe_to_repo_discoveries(self, callback):
    self._repo_discovery_subscribers.remove(callback)

  def subscribe_to_repo_branch_changes(self, callback):
    self._repo_branch_subscribers.append(callback)

  def unsubscribe_to_repo_branch_changes(self, callback):
    self._repo_branch_subscribers.remove(callback)

  def subscribe_to_repo_state_changes(self, callback):
    self._repo_state_subscribers.append(callback)

  def unsubscribe_to_repo_state_changes(self, callback):
    self._repo_state_subscribers.remove(callback)

  def start(self):
    if self._is_running: return
    self._is_running = True
    gobject.idle_add(self._check_stale_repos)

  def stop(self):
    self._is_running = False

  def get_repos_under_path(self, path):
    repos_under_path = []
    for repo in self._repos:
      if repo.path.startswith(path + '/') or \
         repo.path == path or \
         path.startswith(repo.path + '/'):
        repos_under_path.append(repo)
    return repos_under_path

  def _check_stale_repos(self):
    for repo in self._repos_to_update:
      repo.update()
      for callback in self._repo_state_subscribers:
        callback(repo)
      for file_path in self._files_to_update[repo]:
        for callback in self._file_state_subscribers:
          callback(file_path, repo.get_file_state(file_path))
    self._files_to_update.clear()
    self._repos_to_update.clear()
    if self._is_running:
      gobject.timeout_add(500, self._check_stale_repos)

  def _monitor_file_and_dependants(self, repo, file_path):
    # Adds all parent directories up to and including repo.path of file_path as
    # well as all descendent files
    if not repo in self._files_to_update: self._files_to_update[repo] = set()
    self._repos_to_update.add(repo)
    for p in repo.get_file_branch(file_path):
      self._files_to_update[repo].add(p)

  def _get_file_state(self, repo_path, path):
    repo = filter(lambda repo: repo.path == repo_path, self._repos)[0]
    return repo.get_file_state(path)
