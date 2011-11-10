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
import os.path

import gedit
import gtk

from giterdone.filebrowsercontroller import FileBrowserController
from giterdone.repositorymanager import RepositoryManager
from giterdone.repositorymonitor import RepositoryMonitor
from giterdone.repositorypane import RepositoryPane
import giterdone.vcs as vcs
from giterdone.windowcontroller import WindowController

class Giterdone(gedit.Plugin):
  """Main plugin class which handles communication with gedit.

  When the plugin is loaded, activate will be called. When the plugin needs to
  be updated, update_ui will be called. Finally, when the plugin is
  deactivated, (either by disabling the plugin from the plugin manager or
  closing gedit) deactivate is called.
  """

  def __init__(self):
    gedit.Plugin.__init__(self)
    self._init_logger()
    self._modify_icon_theme_lookup()
    vcs.init()
    self._repo_monitor = RepositoryMonitor()
    self._repo_monitor.start()
    self._repo_manager = RepositoryManager(self._repo_monitor)
    self._repo_panes = {} # window -> repository pane
    self._fb_controllers = {} # window -> file browser controller
    self._window_controllers = {} # window -> window controller

  def activate(self, window):
    self._window_controllers[window] = WindowController(
        window, self._repo_monitor, self._repo_manager)
    self._repo_panes[window] = RepositoryPane(
        window, self._repo_monitor, self._repo_manager,
        self._window_controllers[window])
    self._fb_controllers[window] = FileBrowserController(
        window, self._repo_monitor, self._repo_manager,
        self._window_controllers[window])

  def deactivate(self, window):
    self._repo_monitor.stop()
    self._repo_panes[window].deactivate()
    del self._repo_panes[window]
    self._fb_controllers[window].deactivate()
    del self._fb_controllers[window]
    self._window_controllers[window].deactivate()
    del self._window_controllers[window]

  def update_ui(self, window):
    # So far haven't figured out what to do with this event
    pass

  def _init_logger(self):
    logger = logging.getLogger('giterdone')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)-24s - %(levelname)7s - %(message)s")
    log_path = '/tmp/giterdone.log'
    if os.path.exists(log_path): os.remove(log_path)
    log_file = open(log_path, 'w')
    ch = logging.StreamHandler(log_file)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

  def _modify_icon_theme_lookup(self):
    # Append the giterdone icon path to default icon theme's lookup paths
    icon_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             'resources')
    gtk.icon_theme_get_default().append_search_path(icon_path)
