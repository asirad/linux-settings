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
import subprocess

from giterdone.vcs.generic import GenericVcsInterface
import state

class SvnInterface(GenericVcsInterface):

    COMMIT_MSG_IGNORE_LINE = '--This line, and those below, will be ignored--'
    COMMIT_MSG_HEADER = '''
'''+COMMIT_MSG_IGNORE_LINE+'''

To cancel this commit close this file without making a change. To commit,
write your message, then save and close the file.

'''


    def __init__(self):
        super(SvnInterface, self).__init__('svn')


    def find_repo(self, path):
        # iteratively check up the directories for a .svn folder
        cur_dir = path
        while cur_dir != '/':
            if os.path.isdir( os.path.join(cur_dir,'.svn') ): return cur_dir
            cur_dir = os.path.dirname(cur_dir)
        return None


    def status_msg(self, root_path, files=None):
        if files == None:
            proc = subprocess.Popen(['svn', 'status'], cwd=root_path, stdout=subprocess.PIPE)
        else:
            proc = subprocess.Popen(['svn', 'status', '--'] + files, cwd=root_path, stdout=subprocess.PIPE)

        result, stderr = proc.communicate()

        return result


    def status(self, root_path):
        filemap = {}

        proc = subprocess.Popen(['svn', 'status', '--no-ignore'],
                                cwd=root_path, stdout=subprocess.PIPE)
        stmsg, stderr = proc.communicate()

        for line in stmsg.split('\n'):
            if not line: continue
            parts = line.split()
            if len(parts) != 2:
                print 'Badly formatted line: \''+line+'\''
                continue
            path = os.path.join(root_path, parts[1])
            if parts[0] == '?':
                self._recurse_add(filemap, root_path, state.UNTRACKED, path)
            elif parts[0] == 'A':
                self._recurse_add(filemap, root_path, state.STAGED, path)
            elif parts[0] == 'M':
                self._recurse_add(filemap, root_path, state.DIRTY, path)
            elif parts[0] == 'I':
                self._recurse_add(filemap, root_path, state.IGNORED, path)

        return filemap


    def diff(self, paths):
        '''Assumes that all paths are in the same git repository'''

        root_path = self.find_repo(paths[0])

        if not root_path: raise RuntimeError('File not in a svn repository: '+paths[0])

        p = subprocess.Popen(['svn', 'diff', '--'] + paths, cwd=root_path, stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()

        return stdout


    def has_msg(self, commit_msg):
        for line in commit_msg.split('\n'):
            line.strip(' \n')
            if line == self.COMMIT_MSG_IGNORE_LINE: return False
            if line != '': return True
        return False


    def commit_msg_template(self, root_path, paths=None):
        return self.COMMIT_MSG_HEADER + self.status_msg(root_path, paths)


    def _recurse_add(self, filemap, root_path, vcs_state, path):
        prev = filemap[path] if path in filemap else None
        # Overwrite file state based on precedence
        if (vcs_state == state.UNTRACKED) or \
           (vcs_state == state.DIRTY and prev != state.UNTRACKED) or \
           (vcs_state == state.STAGED and not prev in (state.UNTRACKED, state.DIRTY)) or \
           (vcs_state == state.SYNCED and not prev in (state.UNTRACKED, state.DIRTY, state.STAGED)) or \
           (vcs_state == state.IGNORED and not prev in (state.UNTRACKED, state.DIRTY, state.STAGED, state.SYNCED)):
            filemap[path] = vcs_state
        if (path + '/').startswith(root_path + '/'): # Recurse
            self._recurse_add(filemap, root_path, vcs_state, os.path.dirname(path))

    def commit_files(self, paths, commit_msg_path):
        if len(paths) == 0:
            print('SvnInterface.commit_files - no paths specified')
            return

        root_path = self.find_repo(paths[0])

        proc = subprocess.Popen( ['svn', 'commit', '--file='+commit_msg_path, '--'] + paths,
                                 cwd=root_path,
                                 stdout=subprocess.PIPE )
        stdout, stderr = proc.communicate()
        # TODO handle any error cases

    def commit(self, root_path, commit_msg_path):
        proc = subprocess.Popen( ['svn', 'commit', '--file='+commit_msg_path],
                                 cwd=root_path,
                                 stdout=subprocess.PIPE )
        stdout, stderr = proc.communicate()
        # TODO handle any error cases

    def fetch(self, root_path):
        proc = subprocess.Popen( ['svn', 'update'], cwd=root_path, stdout=subprocess.PIPE )
        stdout, stderr = proc.communicate()
        # TODO handle any error cases


    def branch_name(self, root_path):
        return os.path.split(root_path)[-1]
