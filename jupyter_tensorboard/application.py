# -*- coding: utf-8 -*-

import copy
import sys

from notebook import nbextensions, serverextensions, extensions

from . import __version__, __name__ as _pkg_name


class ToggleJupyterTensorboardApp(
        nbextensions.ToggleNBExtensionApp,
        serverextensions.ToggleServerExtensionApp):
    """App to toggle server extension jupyter_nbextensions_configurator."""

    flags = copy.deepcopy(serverextensions.ToggleServerExtensionApp.flags)
    flags['sys-prefix'] = ({
        'ToggleServerExtensionApp': {
            'sys_prefix': True,
            'user': False,
        }},
        'Use sys.prefix as the prefix for configuring extension')
    for f in ('py', 'python'):
        flags.pop(f, None)

    def parse_command_line(self, argv=None):
        """
        Overriden to check for conflicting flags
        Since notebook version doesn't do it well (or, indeed, at all)
        """
        conflicting_flags = set(['--user', '--system', '--sys-prefix'])

        if len(conflicting_flags.intersection(set(argv))) > 1:
            raise serverextensions.ArgumentConflict(
                'cannot specify more than one of user, sys_prefix, or system')
        return super(ToggleJupyterTensorboardApp,
                     self).parse_command_line(argv)

    @property
    def name(self):
        return 'jupyter_tensorboard {}'.format(
            'enable' if self._toggle_value else 'disable')

    @property
    def description(self):
        return """
{} the jupyter_tensorboard extension in config.
Usage
    jupyter tensorboard {} [--system|--sys-prefix|--user]
""".format(*(('Enable', 'enable')
             if self._toggle_value else ('Disable', 'disable')))

    def start(self):
        """Perform the App's actions as configured."""
        if self.extra_args:
            sys.exit('{} takes no extra arguments'.format(self.name))
        else:

            if self._toggle_value:
                nbextensions.install_nbextension_python(
                    _pkg_name, overwrite=True, symlink=False,
                    user=self.user, sys_prefix=self.sys_prefix, prefix=None,
                    nbextensions_dir=None, logger=None)
            else:
                nbextensions.uninstall_nbextension_python(
                    _pkg_name, user=self.user, sys_prefix=self.sys_prefix,
                    prefix=None, nbextensions_dir=None, logger=None)

            self.toggle_nbextension_python(_pkg_name)
            self.toggle_server_extension_python(_pkg_name)


class EnableJupyterTensorboardApp(
        ToggleJupyterTensorboardApp):
    """App to enable server extension jupyter_nbextensions_configurator."""
    name = 'jupyter tensorboard enable'
    _toggle_value = True


class DisableJupyterTensorboardApp(
        ToggleJupyterTensorboardApp):
    """App to disable server extension jupyter_nbextensions_configurator."""
    name = 'jupyter tensorboard disable'
    _toggle_value = False


class JupyterTensorboardApp(extensions.BaseExtensionApp):
    """Root level jupyter_nbextensions_configurator app."""

    name = 'jupyter tensorboard'
    version = __version__
    description = (
        'Enable or disable '
        'the jupyter_tensorboard extension')
    subcommands = dict(
        enable=(
            EnableJupyterTensorboardApp,
            'Enable the jupyter_tensorboard extension.'),
        disable=(
            DisableJupyterTensorboardApp,
            'Disable the jupyter_tensorboard extension.'),
    )
    examples = '\n'.join([
        'jupyter tensorboard enable'
        '  # Enable the jupyter_tensorboard extension.',
        'jupyter tensorboard disable'
        ' # Disable the jupyter_tensorboard extension.',
    ])

    def start(self):
        """Perform the App's actions as configured"""
        super(JupyterTensorboardApp, self).start()

        # The above should have called a subcommand and raised NoStart; if we
        # get here, it didn't, so we should self.log.info a message.
        subcmds = ", ".join(sorted(self.subcommands))
        sys.exit("Please supply at least one subcommand: %s" % subcmds)


main = JupyterTensorboardApp.launch_instance


if __name__ == '__main__':  # pragma: no cover
    main()
