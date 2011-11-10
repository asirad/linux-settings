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

import gtk
import gtk.gdk
import gedit

from giterdone.common import get_icon
from giterdone.repository import Repository
import giterdone.vcs as vcs

class RepositoryPane(gtk.TreeView):
  """A gtk.TreeView that displays a list of the repositories being managed by
  giterdone."""

  _POPUP_XML = '''
      <ui>
        <popup name="RepositoryPanePopup">
          <menuitem action="VcsCommit"/>
        </popup>
      </ui>'''
  _ICON_NAME = 'giterdone-repo-manager'
  _TITLE = 'Repository Manager'
  _COL_REPO = 0
  _COL_NAME = 1
  _COL_BRANCH = 2
  _COL_EMBLEM = 3
  _FB_BUS_ID = '/plugins/filebrowser'
  _FB_ROOT_CHANGED_EVT = 'root_changed'
  _logger = logging.getLogger('giterdone.RepositoryPane')

  def __init__(self, window, repo_monitor, repo_manager, window_controller):
    super(RepositoryPane, self).__init__(gtk.ListStore(object, # repo
                                                       str, # display name
                                                       str, # branch
                                                       gtk.gdk.Pixbuf)) # emblem
    self._curr_root = None
    self._statusbars = {} # statusbar context id -> statusbar
    self._bus_connection_ids = []
    self._window = window
    self._repo_monitor = repo_monitor
    self._repo_monitor.subscribe_to_repo_branch_changes(
        self._on_repo_branch_changed)
    self._repo_monitor.subscribe_to_repo_discoveries(self._add_repo)
    self._repo_monitor.subscribe_to_repo_state_changes(
        self._on_repo_state_changed)
    self._repo_manager = repo_manager
    self._window_controller = window_controller

    # Set up tree view UI
    self.set_grid_lines(False)
    self.set_headers_clickable(True)
    self.append_column(gtk.TreeViewColumn(None, gtk.CellRendererPixbuf(),
                                          pixbuf=RepositoryPane._COL_EMBLEM))
    self.append_column(gtk.TreeViewColumn('Name', gtk.CellRendererText(),
                                          text=RepositoryPane._COL_NAME))
    self.append_column(gtk.TreeViewColumn('Branch', gtk.CellRendererText(),
                                          text=RepositoryPane._COL_BRANCH))
    self.connect('button-release-event', self._on_button_released)

    # Create the repository pane popup
    self.uimanager = gtk.UIManager()
    self.uimanager.add_ui_from_string(RepositoryPane._POPUP_XML)
    self.actiongroup = gtk.ActionGroup('VcsBase')
    # TODO(robert) BEFORE ACTIVATING THESE, USE REPO_MANAGER WHEN DOING VCS
    # COMMANDS
    self.actiongroup.add_actions([
        ('VcsCommit', 'giterdone-commit', 'Commit', None,
            'Commit all staged files', self._on_vcs_commit_all)])
#        ('VcsFetch', gtk.STOCK_GO_DOWN, 'Fetch', None,
#            'Fetch from remote repositories', self._on_vcs_fetch)])
#        ('VcsPush', gtk.STOCK_GOTO_TOP, 'Push', None,
#            'Push to origin repository', self._on_vcs_push),
#        ('VcsPull', gtk.STOCK_GOTO_BOTTOM, 'Pull', None,
#            'Pull from remote reposities', self._on_vcs_pull)])
    self.uimanager.insert_action_group(self.actiongroup, 0)

    self._window.get_side_panel().add_item(
        self, RepositoryPane._TITLE,
        gtk.image_new_from_icon_name(
            RepositoryPane._ICON_NAME, gtk.ICON_SIZE_MENU))
    self._bus_connection_ids.append(window.get_message_bus().connect(
        RepositoryPane._FB_BUS_ID,
        RepositoryPane._FB_ROOT_CHANGED_EVT,
        self._on_fb_root_changed))

  def deactivate(self):
    self._window.get_side_panel().remove_item(self)
    map(self._window.get_message_bus().disconnect, self._bus_connection_ids)
    self._repo_monitor.unsubscribe_to_repo_branch_changes(
        self._on_repo_branch_changed)
    self._repo_monitor.unsubscribe_to_repo_discoveries(self._add_repo)
    self._repo_monitor.unsubscribe_to_repo_state_changes(
        self._on_repo_state_changed)

  def _on_fb_root_changed(self, bus, message):
    """Adds/removes repositories to/from the repository pane based on the new
    root and each repository's path."""
    self._curr_root = message.get_value('uri')[len('file://'):]

    # remove repos from the model
    toremove = []
    for row in self.get_model(): toremove.append(row)
    for row in toremove: self.get_model().remove(row.iter)

    # Add current set of repos
    curr_repos = self._repo_monitor.get_repos_under_path(self._curr_root)
    for repo in curr_repos:
      self._add_repo(repo)

  def _add_repo(self, repo):
    self.get_model().append((
         repo,
         self._generate_repo_name(repo),
         repo.get_branch_name(),
         self._get_emblem(repo)))
    RepositoryPane._logger.info('Added repository %s' % (repo.path,))

  def _on_repo_state_changed(self, repo):
    for row in self.get_model():
      if row[RepositoryPane._COL_REPO] == repo:
        self.get_model().set_value(
            row.iter, RepositoryPane._COL_EMBLEM, self._get_emblem(repo))
        break

  def _on_repo_branch_changed(self, repo):
    # TODO(robert) hook this up to an event
    for row in self.get_model():
      if row[RepositoryPane._COL_REPO] == repo:
        self.get_model().set_value(
            row.iter, RepositoryPane._COL_BRANCH, repo.get_branch_name())
        break

  def _set_action_sensitivities(self):
    model, rows = self.get_selection().get_selected_rows()

    if len(rows) != 1:
      RepositoryPane._logger.info('User selected multiple repositories')
      for action in self.actiongroup.list_actions():
        action.set_sensitive(False)
      return

    repo = model[rows[0]][RepositoryPane._COL_REPO]

    RepositoryPane._logger.info('User selected repository %s' % (repo.path,))

    # activate all commands
    for action in self.actiongroup.list_actions():
      action.set_sensitive(True)

    # don't activate commit if there is nothing staged
    if not repo.has_staged_files():
      RepositoryPane._logger.debug(
          'Deactivating commit action since repository has no staged files')
      self.actiongroup.get_action('VcsCommit').set_sensitive(False)

  def _on_button_released(self, widget, event):
    if event.button == 3: # right-click
      self._set_action_sensitivities()

      # show context menu
      self.uimanager.get_widget('/RepositoryPanePopup').popup(
          None, None, None, event.button, 0)

  def _on_vcs_commit_all(self, action):
    model, rows = self.get_selection().get_selected_rows()

    repo = model[rows[0]][RepositoryPane._COL_REPO]
    self._window_controller.start_commit_edit([repo.path])

  def _on_vcs_pull(self, action):
    model, rows = self.get_selection().get_selected_rows()

    for repo in [row[RepositoryPane._COL_REPO] for row in rows]:
      # TODO(robert) implement
      pass

  def _on_vcs_push(self, action):
    model, rows = self.get_selection().get_selected_rows()

    for repo in [row[RepositoryPane._COL_REPO] for row in rows]:
      # TODO(robert) implement
      pass

  def _on_vcs_fetch(self, action):
    model, rows = self.get_selection().get_selected_rows()

    for repo in [model[row][RepositoryPane._COL_REPO] for row in rows]:
      for context_id, statusbar in self._statusbars.iteritems():
        self._window.get_statusbar().flash_message(
            self._sb_context_id, 'Fetching repository %s' % (repo.path,))
      vcs.interfaces[repo.type].fetch(repo.path)

  def _get_emblem(self, repo):
    return get_icon(repo.get_file_state(repo.path))

  def _generate_repo_name(self, repo):
    if not self._curr_root:
      msg = self._window.get_message_bus().send_sync(RepositoryPane._FB_BUS_ID,
                                                     'get_root')
      self._curr_root = msg.get_value('uri')[len('file://'):]
    if repo.path == self._curr_root: # curr_root is repo
      return os.path.basename(repo.path)
    elif repo.path.startswith(self._curr_root + '/'): # curr_root contains repo
      return '.' + repo.path[len(self._curr_root):]
    else: # curr_root is within repo
      return os.path.basename(repo.path)
