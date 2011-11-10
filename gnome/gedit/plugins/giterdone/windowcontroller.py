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
import os
import tempfile

import gedit

class WindowController(object):
  """Handles processing of commits and watches for saving of files belonging to
  giterdone-managed VCS repositories."""

  _logger = logging.getLogger('giterdone.WindowController')

  def __init__(self, window, repo_monitor, repo_manager):
    self._window = window
    self._repo_monitor = repo_monitor
    self._repo_manager = repo_manager
    self._commit_tabs = {} # commit tab id -> paths
    # Listen for tab closes. These might be vcs commit messages.
    self._tab_removed_connection = self._window.connect('tab-removed',
                                                   self._on_tab_removed)
    # subscribe to save events from all open docs
    self._doc_saved_connections = {}
    for doc in self._window.get_documents():
      WindowController._logger.info('WindowController attatching to document')
      self._doc_saved_connections[doc] = doc.connect('saved', self._on_doc_saved)

    # Listen for tab added
    self._tab_added_connection = self._window.connect('tab-added',
                                                      self._on_tab_added)

  def deactivate(self):
    self._window.disconnect(self._tab_removed_connection)
    self._window.disconnect(self._tab_added_connection)
    for host, conn in self._doc_saved_connections.iteritems():
      # First check if handler is even connected because gedit is not good about
      # maintaining connections when gedit is closing
      if host.handler_is_connected(conn):
        host.disconnect(conn)

  def start_commit_edit(self, paths):
    WindowController._logger.info('Initiated commit message edit')
    # Create and open a document with the commit msg template
    # create temp text file to store commit message
    f = tempfile.NamedTemporaryFile(
        prefix='gedit-commit-message-',
        suffix='.commit', delete=False)
    commit_msg_template = self._repo_manager.get_commit_msg_template(paths)
    if commit_msg_template == None: return
    f.write(commit_msg_template)
    commit_msg_path = f.name
    f.close()

    # Open file in gedit
    tab = self._window.create_tab_from_uri('file://'+commit_msg_path,
                                           gedit.encoding_get_utf8(),
                                           0, False, True)
    self._commit_tabs[tab] = paths
    tab.get_document().goto_line(0)

  def _on_doc_saved(self, doc, _):
    path = doc.get_uri()[len('file://'):]
    self._repo_monitor.update_file(path)

  def _on_tab_added(self, window, tab):
    doc = tab.get_document()
    self._doc_saved_connections[doc] = doc.connect('saved', self._on_doc_saved)

  def _on_tab_removed(self, window, tab):
    # Stop listening for saves
    doc = tab.get_document()
    doc.disconnect(self._doc_saved_connections[doc])
    if tab in self._commit_tabs: # Removed tab that contained commit message
      commit_msg_path = tab.get_document().get_uri()[len('file://'):]
      self._repo_manager.commit_files(self._commit_tabs[tab], commit_msg_path)

      # Clean up by removing temp commit message file and tab entry
      del self._commit_tabs[tab]
      os.remove(commit_msg_path)
