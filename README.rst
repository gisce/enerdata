========
Enerdata
========

A set of energy models

.. image:: https://github.com/gisce/enerdata/actions/workflows/python2-app.yml/badge.svg
    :target: https://github.com/gisce/enerdata/actions/workflows/python2-app.yml

.. image:: https://github.com/gisce/enerdata/actions/workflows/python3-app.yml/badge.svg
    :target: https://github.com/gisce/enerdata/actions/workflows/python3-app.yml
    
.. image:: https://coveralls.io/repos/github/gisce/enerdata/badge.svg?branch=master
    :target: https://coveralls.io/github/gisce/enerdata?branch=master


--------------
Considerations
--------------

Any date instance must be localized, see ``enerdata.datetime.timezone.localize`` method!!

.. code-block:: python

  from enerdata.datetime.timezone import TIMEZONE
  
  TIMEZONE.localize(datetime(2018,2,5,1,0))
  
  
Default timezone ``Europe/Madrid``, it can be changed overriding the TIMEZONE definition




---
TDD
---

With this library we try to do TDD.

.. code-block:: bash

  $ export PYTHONPATH="."
  $ mamba

or if you are working with a virtualenv

.. code-block:: bash

  $ pip install -e .
  $ mamba
