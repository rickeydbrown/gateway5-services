# Custom Ansible callback plugin to output only device_alive status
from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    """
    Custom callback plugin that outputs only the device_alive field
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'is_alive_only'

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.device_alive = None

    def v2_runner_on_ok(self, result):
        """Capture successful task results"""
        # Check if this task set device_alive
        if 'ansible_facts' in result._result and 'device_alive' in result._result['ansible_facts']:
            self.device_alive = result._result['ansible_facts']['device_alive']

    def v2_playbook_on_stats(self, stats):
        """Output the device_alive status at the end"""
        if self.device_alive is not None:
            # Output just true/false (lowercase for JSON compatibility)
            self._display.display(str(self.device_alive).lower())
        else:
            # If no device_alive found, output false
            self._display.display("false")
