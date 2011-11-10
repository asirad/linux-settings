from glib import GError
import gtk

import vcs.state

__all__ = ['emblem_names', 'get_emblem_name', 'compare_versions', 'get_icon']

emblem_names = {
  vcs.state.DIRTY: 'giterdone-dirty',
  vcs.state.STAGED: 'giterdone-staged',
  vcs.state.SYNCED: 'giterdone-synced',
  vcs.state.UNTRACKED: 'giterdone-untracked'
}

icons = None

def load_icon(name):
  """Loads an icon corresponding to a given file name.

  Arguments:
    name: A file name for an icon in the 'resources' folder.

  Returns:
    A gtk.gdk.Pixbuf representation of the icon.
  """
  try:
    return gtk.icon_theme_get_default().load_icon(name, 20, gtk.ICON_LOOKUP_USE_BUILTIN)
  except GError:
    print 'Giterdone: WARNING could not load icon.'
    return None

def init_icons():
  global icons
  icons = {}
  for status_id, emblem_name in emblem_names.iteritems():
    icon = load_icon(emblem_name)
    if icon: icons[status_id] = icon

def get_emblem_name(status_id):
  if not status_id in emblem_names: return None
  return emblem_names[status_id]

def get_icon(status_id):
  if icons == None: init_icons()
  if not status_id in icons: return None
  return icons[status_id]

def compare_versions(v1, v2):
  """Like the Java compareTo method, returns the result of comparing to
  version strings.

  The given versions should be triples of the form (<major>, <minor>,
  <revision>) (e.g. (1,2,10)). If v1 is newer than v2, a positive number is
  returned. If v1 and v2 are the same version, 0 is returned. If v2 is newer
  than v1, a negative number is returned.
  """
  major_diff = v1[0] - v2[0]
  if major_diff != 0: return major_diff
  minor_diff = v1[1] - v2[1]
  if minor_diff != 0: return minor_diff
  return v1[2] - v2[2]
