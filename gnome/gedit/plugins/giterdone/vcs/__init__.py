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

import inspect
import logging
import os
import sys

from giterdone.vcs.generic import GenericVcsInterface
import state

__all__ = ['init', 'interfaces', 'state']

interfaces = {}

def init():
  """Initializes the VCS interfaces by searching the local folder for python
  files that have classes that implement
  giterdone.vcs.generic.GenericVcsInterface.
  """
  logger = logging.getLogger('giterdone.vcs')
  curr_dir = os.path.dirname(os.path.realpath(__file__))

  for filename in os.listdir(curr_dir):
    if not filename.endswith('.py'): continue
    if filename in ('generic.py', '__init__.py', 'state.py'): continue

    module_name = filename[:-len('.py')]
    abs_module_name = 'giterdone.vcs.%s' % (module_name,)
    __import__(abs_module_name)
    module = sys.modules[abs_module_name]

    for name, obj in inspect.getmembers(module):
      if not inspect.isclass(obj): continue
      if not issubclass(obj.__class__, GenericVcsInterface.__class__): continue
      if obj.__name__ == GenericVcsInterface.__name__: continue
      logger.info('Loading vcs interface ' + name)
      interface = obj()
      interfaces[interface.type] = interface
