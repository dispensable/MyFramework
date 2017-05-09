# -*- coding:utf-8 -*-
#!/usr/bin/env python3

import os
import sys


def trans(config, out):
    if not os.path.exists(config):
        raise IOError('config file not exist')

    if not os.path.exists(out):
        raise IOError('out file not exist')

    with open(config, 'r') as f:
        with open(out, 'w+') as fout:
            for setting in f.readlines():
                print('handle {}'.format(setting))
                if setting.startswith('#'):
                    continue
                if not setting:
                    continue
                if '=' in setting:
                    conf, value = setting.split('=')
                    conf.strip()
                    value.lstrip()
                    fout.write('{config}\n{mark}\n\n    默认值:{value}\n'
                               '    可选值:\n\n    说明:\n\n    '
                               '示例:\n\n.. code-block:: python\n\n   {setting}\n'.format(
                        config=conf, mark='^' * (len(conf) - 1), value=value, setting=setting
                    ))
    print('transfer config file to sphinx doc done! check the {}'.format(out))


if __name__ == '__main__':
    _, config, out = sys.argv
    trans(config, out)
