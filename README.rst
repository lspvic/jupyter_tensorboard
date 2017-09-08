Jupyter-Tensorboard: Start tensorboard in Jupyter notebook
=================================================================

|build-status| |pypi-status| |pypi-pyversions| |docker-stars|

Tensorboard Integration for Jupyter Notebook.

A jupyter server extension for jupyter notebook and tensorboard (a visualization tool for tensorflow) which provides graphical user interface for tensorboard start, manage and stop in jupyter interface.

Installation
------------

#.  **Be sure that tensorflow(-gpu)>=1.3.0 has been installed**. If not, you should install or upgrade your tensorflow>=1.3.0 first, and tensorboard is a dependency of tensorflow so that it is automatically installed. This package does not have a tensorflow dependency because there are several distributions of tensorflow, for example, tensorflow and tensorflow-gpu. Any way, you must be sure you have tensorflow(-gpu) installed before install this package.

#.  Install the pip package. The python version must be the same as Jupyter: if you start jupyter notebook in python3, ``pip3`` may be used to install the package

    ``pip(3) install jupyter-tensorboard``

    **NOTE:**

    The python version is important, you must be sure that your *jupyter*, *jupyter_tensorboard*, *tensorflow* have the same python version. If your tensorflow python and jupyter python versions are different, e.g., use tensorflow in py2 but jupyter starts in py3, both versions of tensorflow(py2 and py3) should be installed, and jupyter_tensorboard should install to py3, in accordance with jupyter.

#.  Restart the jupyter notebook server.

Use jupyter-tensorboard in docker containers
++++++++++++++++++++++++++++++++++++++++++++

Docker image for ``Jupyter Notebook Scientific Python Stack + Tensorflow + Tensorboard`` is available, just with the command:

.. code-block:: bash

    docker pull lspvic/tensorboard-notebook
    docker run -it --rm -p 8888:8888 lspvic/tensorboard-notebook

Jupyter notebook with tensorboard integrated is now available in http://localhost:8888 , details are in `docker/README.md <https://github.com/lspvic/jupyter_tensorboard/tree/master/docker/>`_.

Usage
-----

Once `jupyter_tensorboard` is installed and enabled, and your notebook server has been restarted, you should be able to find the interfaces to manage tensorboard instances.

- In notebook tree view, select a directory, a ``tensorboard`` button will be presented. Click the button, a new browser tab will be opened to show the tensorboard interface with the proposed directory as logdir.

.. image:: https://github.com/lspvic/jupyter_tensorboard/raw/master/docs/_static/tensorboard_button.png

- In notebook tree view, click the ``tensorboard`` menu in ``new`` and a new tensorboard instance is started with current directory as logdir.

.. image:: https://github.com/lspvic/jupyter_tensorboard/raw/master/docs/_static/tensorboard_menu.png

- In notebook ``running`` tab, a list of tensorboard instances are showed. Managing operations such as browsing, navigating, shutdown  can be found here. 

.. image:: https://github.com/lspvic/jupyter_tensorboard/raw/master/docs/_static/tensorboard_list.png

- The tensorboard instance interface is in ``http://jupyter-host/tensorboard/<name>/`` with the instance names increasing from 1.

.. image:: https://github.com/lspvic/jupyter_tensorboard/raw/master/docs/_static/tensorboard_url.png

Uninstall
---------
To purge the installation of the extension, there are a few steps to execute:

.. code:: bash

    jupyter tensorboard disable --user
    pip uninstall jupyter-tensorboard

or if you have uninstall the pip package, but the extension seems to be not purged, you can execute:

.. code:: bash

    jupyter serverextension disable --user
    jupyter nbextension disable jupyter_tensorboard/tree --user
    jupyter nbextension uninstall jupyter_tensorboard --user

The commands accept the same flags as the ``jupyter serverextension`` command provided by notebook versions, including ``--system`` to enable(or disable) in system-wide config, or ``--sys-prefix`` to enable(or disable) in config files inside python's ``sys.prefix``, such as for a virtual environment.

Troubleshooting
---------------

If you encounter problems with this server extension, you can:

* Check that tensorflow(-gpu)>=1.3 is installed.
* Check that jupyter-tensorboard is installed via ``pip list|grep jupyter-tensorboard``.
* Check that jupyter, tensorflow and jupyter_tensorboard have the same python version.
* Check the issue page for this repository. If you can't find one that fits your problem, please create a new one!

For debugging, useful information can (sometimes) be found by:

* Checking for error messages in the browser's Javascript console.
* Checking for messages in the notebook server's logs. This is particularly useful when the server is run with the --debug flag, to get as many logs as possible.


.. |build-status| image:: https://img.shields.io/travis/lspvic/jupyter_tensorboard.svg
    :target: https://travis-ci.org/lspvic/jupyter_tensorboard

.. |pypi-status| image:: https://img.shields.io/pypi/v/jupyter_tensorboard.svg
    :target: https://pypi.python.org/pypi/jupyter_tensorboard

.. |pypi-pyversions| image:: https://img.shields.io/pypi/pyversions/jupyter_tensorboard.svg
    :target: https://pypi.python.org/pypi/jupyter_tensorboard

.. |docker-stars| image:: https://img.shields.io/docker/stars/lspvic/tensorboard-notebook.svg
    :target: https://hub.docker.com/r/lspvic/tensorboard-notebook/
