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
        self.command_result = None

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

        # Check for command_result (from run_command_playbook.yml command tasks)
        # Look for stdout from network command modules
        if 'stdout' in result._result and result._result.get('changed') == False:
            # This looks like a command execution result
            task_name = result._task.get_name()
            if 'Execute command' in task_name:
                self.command_result = result._result['stdout']

    def v2_playbook_on_stats(self, stats):
        """Output the appropriate data at the end"""
        import sys
        import json
        # Priority: config_data > command_result > device_alive
        if self.config_data is not None:
            # This was a get_config playbook
            self._display.display(self.config_data)
        elif self.command_result is not None:
            # This was a run_command playbook - output the command results
            # stdout is a list, so join with newlines or output as JSON
            if isinstance(self.command_result, list):
                output = '\n'.join(self.command_result)
            else:
                output = self.command_result
            self._display.display(output)
        elif self.device_alive is not None:
            # This was an is_alive playbook - output plain true/false WITHOUT newline
            # Use print with end='' to match Python script behavior
            print(str(self.device_alive).lower(), end='')
            sys.stdout.flush()
        else:
            # No data found - check if this was an is_alive playbook that succeeded
            # If there are no failures, assume device is alive
            if stats.failures == {} and stats.dark == {}:
                # Playbook succeeded with no failures - device is alive
                print("DEBUG: No device_alive found, but no failures. Outputting 'true'", file=sys.stderr)
                print("true", end='')
                sys.stdout.flush()
            else:
                # Playbook had failures - device is not alive
                print("DEBUG: Playbook had failures. Outputting 'false'", file=sys.stderr)
                print("false", end='')
                sys.stdout.flush()
