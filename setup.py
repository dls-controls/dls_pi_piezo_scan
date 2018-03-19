from setuptools import setup

# these lines allow the version to be specified in Makefile.private
import os
version = os.environ.get("MODULEVER", "0.0")

setup(
#    install_requires = ['cothread'], # require statements go here
    name = 'dls_pi_piezo_scan',
    version = version,
    description = 'Module',
    author = 'tdq39642',
    author_email = 'tdq39642@fed.cclrc.ac.uk',
    packages = ['dls_pi_piezo_scan'],
#    entry_points = {'console_scripts': ['test-python-hello-world = dls_pi_piezo_scan.dls_pi_piezo_scan:main']}, # this makes a script
#    include_package_data = True, # use this to include non python files
    zip_safe = False
    )
