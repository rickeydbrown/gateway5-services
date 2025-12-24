#!/usr/bin/python
# Custom Ansible module to extract and output device configuration

import re
from ansible.module_utils.basic import AnsibleModule


def run_module():
    module_args = dict(
        config_results=dict(type='dict', required=True),
        platform=dict(type='str', required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    cfg_data = ""

    # Grab the config results from stdout
    config_results = module.params['config_results']
    platform = module.params['platform']

    # Handle skipped tasks - check if this task actually ran
    if config_results.get('skipped', False):
        module.exit_json(changed=False, skipped=True, msg='Command was skipped')

    if 'stdout' not in config_results or not config_results['stdout']:
        module.fail_json(msg='No stdout found in config_results', config_results=config_results)

    cfg_line = config_results['stdout'][0]

    # For IOS-XR, skip the "Building configuration..." line
    if platform == 'iosxr':
        configObj = re.match(r'Building configuration...\n(.*)', cfg_line, re.M | re.I | re.S)
        if configObj is not None:
            cfg_data = configObj.group(1)
        else:
            cfg_data = cfg_line
    else:
        cfg_data = cfg_line

    # Output just the configuration data
    module.exit_json(changed=False, config_data=cfg_data)


def main():
    run_module()


if __name__ == '__main__':
    main()
