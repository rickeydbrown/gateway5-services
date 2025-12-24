# Custom Ansible callback plugin for Itential Gateway output
from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    """
    Custom callback plugin that outputs only relevant data for Itential Gateway:
    - For get_config: outputs config_data field
    - For is_alive: outputs device_alive boolean
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'itential_output'

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.config_data = None
        self.device_alive = None

    def v2_runner_on_ok(self, result):
        """Capture successful task results"""
        # Check for config_data (from get_config_output module)
        if 'config_data' in result._result:
            self.config_data = result._result['config_data']

        # Check for device_alive (from set_fact)
        if 'ansible_facts' in result._result and 'device_alive' in result._result['ansible_facts']:
            self.device_alive = result._result['ansible_facts']['device_alive']
            # Debug output to stderr
            import sys
            print(f"DEBUG: Found device_alive = {self.device_alive} (type: {type(self.device_alive)})", file=sys.stderr)

    def v2_playbook_on_stats(self, stats):
        """Output the appropriate data at the end"""
        # Priority: config_data > device_alive
        if self.config_data is not None:
            # This was a get_config playbook
            self._display.display(self.config_data)
        elif self.device_alive is not None:
            # This was an is_alive playbook
            self._display.display(str(self.device_alive).lower())
        else:
            # No data found - could be an error
            self._display.display("ERROR: No output data found", color='red')
