# Custom Ansible callback plugin to output only config_data
from ansible.plugins.callback import CallbackBase
import json


class CallbackModule(CallbackBase):
    """
    Custom callback plugin that outputs only the config_data field
    from the get_config_output module result
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'config_data_only'

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.config_data = None

    def v2_runner_on_ok(self, result):
        """Capture successful task results"""
        # Check if this is the get_config_output task with config_data
        if 'config_data' in result._result:
            self.config_data = result._result['config_data']

    def v2_playbook_on_stats(self, stats):
        """Output the config_data at the end"""
        if self.config_data:
            # Output just the config_data
            self._display.display(self.config_data)
        else:
            # If no config_data found, output empty string or error
            self._display.display("ERROR: No config_data found", color='red')
