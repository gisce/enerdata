========
Enerdata
========

A set of energy models

.. image:: https://github.com/gisce/enerdata/actions/workflows/python2.7-app.yml/badge.svg
    :target: https://github.com/gisce/enerdata/actions/workflows/python2.7-app.yml

.. image:: https://github.com/gisce/enerdata/actions/workflows/python3.6-app.yml/badge.svg
    :target: https://github.com/gisce/enerdata/actions/workflows/python3.6-app.yml

.. image:: https://github.com/gisce/enerdata/actions/workflows/python3.7-app.yml/badge.svg
    :target: https://github.com/gisce/enerdata/actions/workflows/python3.7-app.yml

.. image:: https://github.com/gisce/enerdata/actions/workflows/python3.8-app.yml/badge.svg
    :target: https://github.com/gisce/enerdata/actions/workflows/python3.8-app.yml

.. image:: https://github.com/gisce/enerdata/actions/workflows/python3.9-app.yml/badge.svg
    :target: https://github.com/gisce/enerdata/actions/workflows/python3.9-app.yml

.. image:: https://github.com/gisce/enerdata/actions/workflows/python3.10-app.yml/badge.svg
    :target: https://github.com/gisce/enerdata/actions/workflows/python3.10-app.yml

.. image:: https://github.com/gisce/enerdata/actions/workflows/python3.11-app.yml/badge.svg
    :target: https://github.com/gisce/enerdata/actions/workflows/python3.11-app.yml

.. image:: https://coveralls.io/repos/github/gisce/enerdata/badge.svg?branch=master
    :target: https://coveralls.io/github/gisce/enerdata?branch=master


--------------
Considerations
--------------

Any date instance must be localized. See ``enerdata.datetime.timezone.localize`` method!!!

.. code-block:: python

  from enerdata.datetime.timezone import TIMEZONE
  
  TIMEZONE.localize(datetime(2018, 2, 5, 1, 0))
  
  
Default timezone is set to ``Europe/Madrid``. It can be changed overriding the TIMEZONE definition.
