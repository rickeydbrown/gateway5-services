#!/usr/bin/env python3
"""
Extract configuration from Ansible JSON output
"""
import json
import sys

def extract_config_from_ansible_json(data):
    """Extract the clean configuration from Ansible JSON output"""
    try:
        # Navigate through the JSON structure
        for play in data.get('plays', []):
            for task in play.get('tasks', []):
                # Look for the "Output just the configuration" task
                if task.get('task', {}).get('name') == 'Output just the configuration':
                    # Get the first host's output
                    hosts = task.get('hosts', {})
                    for hostname, result in hosts.items():
                        if 'msg' in result:
                            return result['msg']

                # Alternative: look for clean_config fact
                if task.get('task', {}).get('name', '').startswith('Extract configuration'):
                    hosts = task.get('hosts', {})
                    for hostname, result in hosts.items():
                        if 'ansible_facts' in result and 'clean_config' in result['ansible_facts']:
                            return result['ansible_facts']['clean_config']

        # Fallback: try to find stdout from command execution
        for play in data.get('plays', []):
            for task in play.get('tasks', []):
                if 'command' in task.get('task', {}).get('name', '').lower():
                    hosts = task.get('hosts', {})
                    for hostname, result in hosts.items():
                        if 'stdout' in result and result['stdout']:
                            config = result['stdout'][0] if isinstance(result['stdout'], list) else result['stdout']
                            # Strip "Building configuration..." line for IOS-XR
                            if config.startswith('Building configuration...'):
                                lines = config.split('\n')
                                return '\n'.join(lines[1:])
                            return config

        return None
    except Exception as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        return None

if __name__ == '__main__':
    try:
        # Read JSON from stdin
        data = json.load(sys.stdin)

        # Extract configuration
        config = extract_config_from_ansible_json(data)

        if config:
            print(config)
            sys.exit(0)
        else:
            print("Could not extract configuration from Ansible output", file=sys.stderr)
            sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
