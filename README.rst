ChromeDriver Installer for Python
=================================

Install `ChromeDriver executable <https://sites.google.com/a/chromium.org/chromedriver/>`__
with **pip**, **easy_install** and **setup.py**.

Usage
-----

Manual Installation
^^^^^^^^^^^^^^^^^^^

Clone the repository:

.. code-block:: bash

    (e)$ git clone https://github.com/peterhudec/chromedriver_installer.git

Install the most recent ChromeDriver version without verifying checksum.

.. code-block:: bash

    (e)$ python setup.py install

Install specific ChromeDriver version without verifying checksum.

.. code-block:: bash

    (e)$ python setup.py install --chromedriver-version=2.10

Install specific ChromeDriver version and verify checksum.
Note that you can pass multiple coma-separated checksums to the
``--chromedriver-checksums`` option. This is useful if you plan to install
ChromeDriver on various platforms because there is separate version with
different checksum for each platform.

.. code-block:: bash

    (e)$ python setup.py install \
        --chromedriver-version=2.10 \
        --chromedriver-checksums=4fecc99b066cb1a346035bf022607104,058cd8b7b4b9688507701b5e648fd821

After install, there should be the ``chromedriver`` executable
available in your path.

.. code-block:: bash

    (e)$ which chromedriver
    /home/andypipkin/e/bin/chromedriver
    (e)$ chromedriver --version
    ChromeDriver 2.10.267518
    (e)$ chromedriver
    Starting ChromeDriver (v2.10.267518) on port 9515
    Only local connections are allowed.


Installation with PIP
^^^^^^^^^^^^^^^^^^^^^

The same as before except you need to pass the install options wrapped in pip's
``--install-option=""`` option.

.. code-block:: bash

        (e)$ pip install chromedriver_installer \
            --install-option="--chromedriver-version=2.10" \
            --install-option="--chromedriver-checksums=4fecc99b066cb1a346035bf022607104,058cd8b7b4b9688507701b5e648fd821"

Testing
-------

You need `tox <https://testrun.org/tox/latest/>`__ to run the tests.

.. code-block:: bash

    (e)$ git clone https://github.com/peterhudec/chromedriver_installer.git
    (e)$ pip install -r requirements.txt
    (e)$ tox
