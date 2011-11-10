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

from giterdone.vcs import interfaces
import giterdone.vcs.state as state

class Repository:
  """This class represents the state of a VCS repository.

  The class has a repository type (e.g git, svn, cvs), an absolute path to the
  root of the repository, and the ability to return the state of any file in it.
  """

  def __init__(self, type, path):
    """Creates a Repository.

    Arguments:
      type <string> Can be 'git' or 'svn' at the moment.
      path <string> Absolute path to the root of the repository.
    """
    if not type: raise TypeError('type')
    if not path: raise TypeError('path')
    self.type = type
    self.path = path
    self._files = {} # file path -> state
    self._states = {
      state.UNTRACKED: [],
      state.IGNORED: [],
      state.SYNCED: [],
      state.STAGED: [],
      state.DIRTY: []
    } # state -> list(file path)

  def update(self):
    """Updates the states of all the files within this repository."""
    self._files = interfaces[self.type].status(self.path)
    for vcs_state in self._states: self._states[vcs_state] = []
    for path, vcs_state in self._files.iteritems():
      self._states[vcs_state].append(path)

  def get_file_state(self, path):
    """Returns the VCS state of a repository file or None if the file is
    not in the repository.
    """
    # Make sure path is in this repository
    if not (path.startswith(self.path + '/') or path == self.path): return None
    return self._files[path] if path in self._files else state.SYNCED

  def has_staged_files(self):
    """Returns true if this repository has staged files, False otherwise."""
    return len(self._states[state.STAGED]) > 0

  def get_branch_name(self):
    """Returns the name of the active branch for this repository."""
    return interfaces[self.type].branch_name(self.path)

  def get_file_branch(self, path):
    """Returns a list of paths from the root of the repo down to the path,
    appended with all of the files within path."""
    branch = []
    # first add ancestors (including path)
    curr_ancestor = path
    while (curr_ancestor + '/').startswith(self.path + '/'):
      branch.append(curr_ancestor)
      curr_ancestor = os.path.dirname(curr_ancestor)
    # now add children
    for p in self._files:
      if p.startswith(path + '/'): # this does not include path itself
        branch.append(p)
    return branch

  def __hash__(self):
    return hash(self.path)

  def __eq__(self, other):
    if not other: return False
    return self.path == other.path

  def __ne__(self, other):
    return not (self == other)
