# Copyright 2013 Walter Scheper
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from cliff import app
from cliff import commandmanager

from hasher import __version__
import logging


class HasherApp(app.App):
    """
    Hasher App
    """

    log = logging.getLogger(__name__)

    def __init__(self):
        super(HasherApp, self).__init__(
            description='',
            version='{0}.{1}.{2}{3}'.format(*__version__),
            command_manager=commandmanager.CommandManager('hasher'),
            )

    def initialize_app(self, argv):
        self.log.debug('Initialize app')

    def prepare_to_run_command(self, cmd):
        self.log.debug('prepare_to_run_command %s', cmd.__class__.__name__)

    def clean_up(self, cmd, result, err):
        self.log.debug('clean_up %s', cmd.__class__.__name__)
        if err:
            self.log.debug('got an error: %s', err)
