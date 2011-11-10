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

class GenericVcsInterface(object):
  """Represents a generic interface to a source version control system."""

  _logger = logging.getLogger('giterdone.vcs.GenericVcsInterface')

  def __init__(self, type):
    """This is meant to be called only by subclasses.

    Arguments:
      type <string> Identifies the type of vcs (e.g. 'git', 'svn', 'cvs',
          'bazaar')
    """
    self.type = type

  def status(self, path):
    """Determines the vcs status of a given path.

    If an error is encountered while determining the status of the given path,
    the error should be logged and a dictionary with names mapping to empty
    lists should be returned.

    Note that this method should be optimized as it will be used periodically
    to check if the repository has changed.

    Arguments:
      path <string> Should be an absolute path under a VCS.

    Returns:
      A dictionary that maps VCS states <giterdone.vcs.state> to lists of
      filepaths <[string]> where each filepath within a list shares the same VCS
      state.
    """
    print 'GenericVcsInterface.status not implemented'
    return None

  def add(self, paths):
    """Places the given paths under vcs and/or (for some vcss) adds them to the
    staging area.

    Arguments:
      paths [list<string>] should be a list of absolute paths.
    """
    print 'GenericVcsInterface.add not implemented'
    return None

  def reset(self, paths):
    """Restores the given paths to the latest commit.

    Arguments:
      paths <[string]> should be a list of absolute paths.
    """
    print 'GenericVcsInterface.reset not implemented'
    return None

  def checkout(self, paths):
    """Checkout out paths from HEAD and overwrite any changes to local file.

    Arguments:
      paths <[string]> List of absolute paths to checkout.
    """
    GenericVcsInterface._logger.error('checkout not implemented')
    return None

  def commit(self, root_path):
    """Commits all staged files in the repository.

    Arguments:
      root_path <string> absolute path to the root directory of the repository.
      commit_msg_path <string> absolute path to a file which contains the commit
          message.
    """
    print 'GenericVcsInterface.commit not implemented'
    return None

  def commit_files(self, paths):
    """Commits only given paths.

    Arguments:
      paths <[string]> absolute paths to commit.
      commit_msg_path <string> absolute path to a file which contains the commit
          message.
    """
    print 'GenericVcsInterface.commit_files not implemented'
    return None

  def fetch(self, root_path):
    """Updates(or fetches) a repository.

    Arguments:
      root_path <string> absolute path the root directory of the repository.
    """
    print 'GenericVcsInterface.fetch not implemented'
    return None

  def find_repo(self, path):
    """Finds the root directory of the repository of which 'path' is in.

    Note that this should be optimized at finding the repository root as it will
    be used often.

    Arguments:
      path <string> Absolute path of where the search will start.

    Returns:
      The absolute path <string> to the root directory of the repository or None
      if the given path is not under a VCS.
    """
    print 'GenericVcsInterface.find_repo not implemented'
    return None

  def diff(self, paths):
    """Diffs the given paths.

    Arguments:
      paths [list<string>] absolute paths to diff.

    Returns:
      The output <string> of diff-ing the given paths against the HEAD of the
      repository.
    """
    print 'GenericVcsInterface.diff not implemented'
    return None

  def status_msg(self, root_path, files=None):
    """Returns the status message executed at the repository root.

    Arguments:
      root_path <string> absolute path to the repository root folder.
      files [list<string>] paths to be included in the status command execution.
    """
    print 'GenericVcsInterface.status_msg not implemented'
    return None

  def has_msg(self, commit_msg):
    """Returns True if the given commit message has an actual message and not
    the just the default template. This is used when determining whether to
    execute a commit.

    Arguments:
      commit_msg <string> candidate commit message.
    """
    print 'GenericVcsInterface.has_msg not implemented'
    return None

  def commit_msg_template(self, root_path, paths=None):
    """Returns a message template used in a commit message.

    Arguments:
      root_path <string> Absolute path to a repository which to generate the
          commit message template for.
      paths <[string]> Paths used in generating the template. If not specified,
          this function generates a template for committing the entire
          repository.
    """
    print 'GenericVcsInterface.commit_msg_template not implemented'
    return None

  def branch_name(self, root_path):
    """Returns the name of the current branch of a repository.

    Arguments:
      root_path <string> Absolute path to a given repository.
    """
    print 'GenericVcsInterface.branch_name not implemented'
    return None
