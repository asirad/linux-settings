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
from urllib import unquote_plus

import gedit
import gobject
import gtk

from giterdone.common import compare_versions
from giterdone.common import get_emblem_name

class FileBrowserController(object):

  _CONTEXT_MENU_PLACEHOLDER = '/FilePopup/FilePopup_Opt3'
  _FB_BUS_ID = '/plugins/filebrowser'
  _logger = logging.getLogger('giterdone.FileBrowserController')

  def __init__(self, window, repo_monitor, repo_manager, window_controller):
    self._window = window
    self._statusbar_id = \
        self._window.get_statusbar().get_context_id('giterdone')
    self._repo_monitor = repo_monitor
    self._repo_monitor.subscribe_to_file_changes(self._on_file_state_changed)
    self._repo_manager = repo_manager
    self._window_controller = window_controller
    mb = self._window.get_message_bus()
    self._on_mb_registered_connection = \
        mb.connect_after('registered', self._on_mb_registered)
    self._on_mb_unregistered_connection = \
        mb.connect_after('unregistered', self._on_mb_unregistered)
    self._connect_to_filebrowser()

  def _connect_to_filebrowser(self):
    self._will_connect_with_fb = False
    self._fb_action_ids = {}
    self._fb_context_ids = []
    self.ids = {} # file path -> gtk.TreeViewRowIter
    mb = self._window.get_message_bus()

    # Get a reference to the file browser view
    self._fb_view = None
    if compare_versions(gedit.version, (2, 27, 5)) >= 0:
      # if version is recent enough, we can use the message bus to get the
      # fb widget
      if mb.is_registered(FileBrowserController._FB_BUS_ID, 'get_view'):
        msg = mb.send_sync(FileBrowserController._FB_BUS_ID, 'get_view')
        self._fb_view = msg.get_value('view')
    else:
      # if version is too old, we have to walk the widget tree to find the
      # fb widget
      for child in self._window.get_side_panel().get_children():
        if isinstance(child, gtk.Notebook):
          for page in child.get_children():
            if page.get_name() == 'GeditFileBrowserWidget':
              self._fb_view = page.get_children()[2].get_children()[0]
              break
          break

    if not self._fb_view:
      FileBrowserController._logger.error(
          'Unable to get reference to FileBrowser plugin\'s view. Perhaps ' \
          'using an older version of gedit.')
      return

    if compare_versions(gedit.version, (2,27,4)) >= 0:
      # !! As of gedit version 2.28.0 (and probably before) this call will
      # cause a warning if the plugin is activated, deactivated, and
      # reactivated in one gedit session because the FB does not properly
      # remove the context item via the message 'remove_context_item'.
      # This results in having to reboot gedit if you want to reactivate
      # (which doesn't happen much anyway).
      # TODO(robert) Will submit fix to gedit team.
      self._add_context_menu_item('vcs-add', 'Vcs add',
                                  'Add file to staging area',
                                  'giterdone-add', self._on_vcs_add,
                                  self._fb_view)
      self._add_context_menu_item('vcs-reset', 'Vcs reset',
                                  'Reset file from staging area',
                                  'giterdone-reset', self._on_vcs_reset,
                                  self._fb_view)
      self._add_context_menu_item('vcs-checkout', 'Vcs checkout',
                                  'Checkout (revert changes to) files',
                                  'giterdone-checkout', self._on_vcs_checkout,
                                  self._fb_view)
      self._add_context_menu_item('vcs-commit', 'Vcs commit',
                                  'Commit staged files',
                                  'giterdone-commit', self._on_vcs_commit,
                                  self._fb_view)
      self._add_context_menu_item('vcs-diff', 'Vcs diff',
                                  'Diff file',
                                  'giterdone-diff', self._on_vcs_diff,
                                  self._fb_view)

      self._fb_selection_changed_conn = self._fb_view.get_selection().connect(
          'changed', self._on_fb_selection_changed)

    # Add listeners to file browser events
    self.bus_ids = []
    self.bus_ids.append(mb.connect(FileBrowserController._FB_BUS_ID,
                                   'inserted', self._on_fb_inserted))
    self.bus_ids.append(mb.connect(FileBrowserController._FB_BUS_ID,
                                   'deleted', self._on_fb_deleted))
    self.bus_ids.append(mb.connect(FileBrowserController._FB_BUS_ID,
                                   'root_changed', self._on_fb_root_changed))

    msg = mb.send_sync(FileBrowserController._FB_BUS_ID, 'get_root')
    uri = msg.get_value('uri')
    self._is_root_local = uri.startswith('file://') if uri else False
    mb.send_sync(FileBrowserController._FB_BUS_ID, 'refresh')

  def deactivate(self):
    # unsubscribe from repository monitor
    self._repo_monitor.unsubscribe_to_file_changes(self._on_file_state_changed)
    bus = self._window.get_message_bus()
    bus.handler_disconnect(self._on_mb_registered_connection)
    bus.handler_disconnect(self._on_mb_unregistered_connection)

    if not self._fb_view: return

    # disconnect all of the actions of the Filebrowser's context menu
    for action, id in self._fb_action_ids.iteritems(): action.disconnect(id)

    if self._fb_view.get_selection():
      self._fb_view.get_selection().disconnect(self._fb_selection_changed_conn)

    # remove context items from FB
    for id in self._fb_context_ids:
      bus.send_sync(FileBrowserController._FB_BUS_ID,
                    'remove_context_item', id=id)

    map(bus.disconnect, self.bus_ids)

    # We need to reload the files in the file browser to get rid of their
    # emblems
    msg = bus.send_sync(FileBrowserController._FB_BUS_ID, 'get_root' )
    bus.send_sync(FileBrowserController._FB_BUS_ID, 'refresh')

  def _on_mb_registered(self, bus, msg_type):
    """Invoked when a message is registered with the gedit message bus.

    If a registration is from the Filebrowser plugin, this controller will
    connect with the plugin.
    """
    if self._will_connect_with_fb: return
    if msg_type.get_object_path() == FileBrowserController._FB_BUS_ID:
      self._will_connect_with_fb = True
      # Connect to the Filebrowser after 1 second to allow it to finish booting
      gobject.timeout_add(1000, self._connect_to_filebrowser)

  def _on_mb_unregistered(self, bus, msg_type):
    """Invoked when a message is unregistered from the gedit message bus.

    If an unregistration is from the Filebrowser, set a flag so this controller
    won't try to access it thereafter.
    """
    if msg_type.get_object_path() == FileBrowserController._FB_BUS_ID:
       self._fb_view = None
       self._will_connect_with_fb = False

  def _on_fb_inserted(self, bus, message):
    if not self._is_root_local: return

    fb_row_id = message.get_value('id')
    uri = message.get_value('uri')
    path = unquote_plus(uri[len('file://'):])

    if self._repo_monitor.update_file(path):
      self.ids[path] = fb_row_id

  def _on_fb_deleted(self, bus, message):
    pass

  def _on_fb_root_changed(self, bus, message):
    self._is_root_local = message.get_value('uri').startswith('file://')

  def _on_fb_selection_changed(self, selection):
    """Activates or deactivates all of the actions in the FileBrowser depending
    on the file selection."""
    paths = self._get_selected_paths(selection)
    if not paths or not self._repo_manager.in_same_repo(paths):
      for action in self._fb_action_ids.keys(): action.set_sensitive(False)
    else:
      for action in self._fb_action_ids.keys():
        if action.get_name() in ('vcs-diff', 'vcs-checkout') and \
           not self._repo_manager.any_are_dirty(paths):
          action.set_sensitive(False)
        elif action.get_name() == 'vcs-add' and \
             not self._repo_manager.any_are_untracked_or_dirty(paths):
          action.set_sensitive(False)
        elif action.get_name() == 'vcs-reset' and \
             not self._repo_manager.any_are_staged(paths):
          action.set_sensitive(False)
        elif action.get_name() == 'vcs-commit' and \
             self._repo_manager.all_are_synced(paths):
          action.set_sensitive(False)
        else:
          action.set_sensitive(True)

  def _on_file_state_changed(self, path, new_state):
    if not self._fb_view: return
    if not path in self.ids: return # ignore paths not shown in FileBrowser
    emblem = get_emblem_name(new_state)
    if emblem:
      self._window.get_message_bus().send(
          FileBrowserController._FB_BUS_ID, 'set_emblem',
          id=self.ids[path], emblem=emblem)

  def _add_context_menu_item(self, name, test, desc, icon, callback, view):
    """Creates an action to be placed in the Filebrowser's context menu and
    updates some collections to keep track of what to remove when the plugin
    is deactivated."""
    action = gtk.Action(name, test, desc, icon)
    self._fb_action_ids[action] = action.connect('activate', callback, view)
    msg = self._window.get_message_bus().send_sync(
        FileBrowserController._FB_BUS_ID,
        'add_context_item',
        action=action,
        path=FileBrowserController._CONTEXT_MENU_PLACEHOLDER)
    self._fb_context_ids.append(msg.get_value('id'))

  def _on_vcs_add(self, action, view):
    FileBrowserController._logger.info('User triggered VCS add')
    paths = self._get_selected_paths_from_view(view)
    if not paths: return
    self._repo_manager.add(paths)
    # flash statusbar message
    msg = 'Added ' + str(len(paths)) + ' files'
    self._window.get_statusbar().flash_message(self._statusbar_id, msg)

  def _on_vcs_reset(self, action, view):
    FileBrowserController._logger.info('User triggered VCS reset')
    paths = self._get_selected_paths_from_view(view)
    if not paths: return
    self._repo_manager.reset(paths)
    # flash statusbar message
    msg = 'Reset %d files' % (len(paths),)
    self._window.get_statusbar().flash_message(self._statusbar_id, msg)

  def _on_vcs_checkout(self, action, view):
    FileBrowserController._logger.info('User triggered VCS checkout')
    paths = self._get_selected_paths_from_view(view)
    if not paths: return
    self._repo_manager.checkout(paths)
    # Flash statusbar message
    msg = 'Checked out %d files' % (len(paths),)
    self._window.get_statusbar().flash_message(self._statusbar_id, msg)

  def _on_vcs_commit(self, action, view):
    FileBrowserController._logger.info('User triggered VCS commit')
    paths = self._get_selected_paths_from_view(view)
    if not paths: return
    self._window_controller.start_commit_edit(paths)

  def _on_vcs_diff(self, action, view):
    FileBrowserController._logger.info('User triggered VCS diff')
    paths = self._get_selected_paths_from_view(view)
    if not paths: return
    self._repo_manager.diff(paths)

  def _get_selected_paths_from_view(self, view):
    return self._get_selected_paths(view.get_selection())

  def _get_selected_paths(self, selection):
    model, rows = selection.get_selected_rows()
    return [model[row][2][len('file://'):] for row in rows]
