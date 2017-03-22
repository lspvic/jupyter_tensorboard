Jupyter-Tensorboard: Start tensorboard in Jupyter notebook
=================================================================

Tensorboard Integration for Jupyter Notebook.

A jupyter server extension for jupyter notebook and tensorboard (a visualization tool for tensorflow) which provides graphical user interface for tensorboard start, manage and stop in jupyter interface.

Installation
------------

1.  Install the pip package. This should be as simple as

    ``pip install jupyter_tensorboard``

2.  Enabling the notebook server to load the server extension. A `jupyter` subcommand is provided for this. You can enable the serverextension and the configurator nbextensions listed below for the current user with

    ``jupyter tensorboard enable --user``


The command accepts the same flags as the ``jupyter serverextension`` command provided by notebook versions >= 5.0, including ``--system`` to enable in system-wide config (the default), or ``--sys-prefix`` to enable in config files inside python's ``sys.prefix``, such as for a virtual environment. The provided ``jupyter tensorboard`` command can also be used to ``disable``.

Once installed, you'll need to restart the notebook server. Once restarted, you should be able to find the tensorboard user interfaces as described below.

Usage
-----

Once `jupyter_tensorboard` is installed and enabled, and your notebook server has been restarted, you should be able to find the interfaces to manage tensorboard instances.

- In notebook tree view, select a directory, a ``tensorboard`` button will be presented. Click the button, a new browser tab will be opened to show the tensorboard interface with the proposed directory as logdir.

.. image:: https://github.com/lspvic/jupyter_tensorboard/raw/master/docs/_static/tensorboard_button.png

- In notebook tree view, click the ``tensorbaord`` menu in ``new`` and a new tensorbaord instance is started with current directory as logdir.

.. image:: https://github.com/lspvic/jupyter_tensorboard/raw/master/docs/_static/tensorboard_menu.png

- In notebook ``running`` tab, a list of tensorboard instances are showed. Managing operations such as browsing, navigating, shutdown  can be found here. 

.. image:: https://github.com/lspvic/jupyter_tensorboard/raw/master/docs/_static/tensorboard_list.png

- The tensorbaord instance interface is in ``http://jupyter-host/tensorboard/<name>/`` with the instance names increasing from 1.

.. image:: https://github.com/lspvic/jupyter_tensorboard/raw/master/docs/_static/tensorboard_url.png

Troubleshooting
---------------

If you encounter problems with this server extension, you can:

* check the issue page for this repository. If you can't find one that fits your problem, please create a new one!

For debugging, useful information can (sometimes) be found by:

* Checking for error messages in the browser's Javascript console.
* Checking for messages in the notebook server's logs. This is particularly useful when the server is run with the --debug flag, to get as many logs as possible.