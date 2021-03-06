# -*- coding: utf-8 -*-

"""See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

import Blaeu

here = path.abspath(path.dirname(__file__))
readme_rst = 'README.rst'

# Get the long description from the README file
if not path.exists(readme_rst):  # TODO: and test it is newer than README.md
    import pypandoc

    rst = pypandoc.convert('README.md', 'rst')
    f = open(readme_rst, 'w+')
    f.write(rst)
    f.close()
with open(path.join(here, readme_rst), encoding='utf-8') as f:
    long_description = f.read()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.
setup(
    name='blaeu',  # Required

    # Versions should comply with PEP 440:
    # https://www.python.org/dev/peps/pep-0440/
    version=Blaeu.VERSION,  # Required

    # This is a one-line description or tagline of what your project does. This
    # corresponds to the "Summary" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#summary
    description='Tools to create (and analyze) RIPE Atlas network measurements',
    # Required

    # This field corresponds to the "Description" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#description-optional
    long_description=long_description,  # Optional

    # This should be a valid link to your project's main homepage.
    #
    # This field corresponds to the "Home-Page" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#home-page-optional
    url='https://framagit.org/bortzmeyer/blaeu',  # Optional

    # This should be your name or the name of the organization which owns the
    # project.
    author='Stéphane Bortzmeyer',  # Optional

    # This should be a valid email address corresponding to the author listed
    # above.
    author_email='stephane+frama@bortzmeyer.org',  # Optional

    license='BSD',

    # Classifiers help users find your project by categorizing it.
    #
    # For a list of valid classifiers, see
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: System Administrators',
        'Intended Audience :: Telecommunications Industry',

        'Topic :: System :: Networking',

        # Pick your license as you wish
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3'
    ],

    # This field adds keywords for your project which will appear on the
    # project page. What does your project relate to?
    #
    # Note that this is a string of words separated by whitespace, not a list.
    keywords='networking atlas monitoring ip ping traceroute dig',  # Optional

    # You can just specify package directories manually here if your project is
    # simple. Or you can use find_packages().
    #
    # Alternatively, if you just want to distribute a single Python file, use
    # the `py_modules` argument instead as follows, which will expect a file
    # called `my_module.py` to exist:
    #
    py_modules=["Blaeu"],
    #
    packages=[],  # Required

    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    #
    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['cymruwhois', 'pyopenssl'],  # Optional

    # List additional groups of dependencies here (e.g. development
    # dependencies). Users will be able to install these using the "extras"
    # syntax, for example:
    #
    #   $ pip install sampleproject[dev]
    #
    # Similar to `install_requires` above, these must be valid existing
    # projects.
    extras_require={
        'dev': ['pypandoc']
        # Optional
    },

    python_requires='>=3',

    # If there are data files included in your packages that need to be
    # installed, specify them here.
    #
    # If using Python 2.6 or earlier, then these have to be included in
    # MANIFEST.in as well.
    package_data={  # Optional
    },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files
    #
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    data_files=[],  # Optional

    # To provide executable scripts, entry points are officially
    # recommended but way too hard for me.
    scripts=['blaeu-reach', 'blaeu-resolve', 'blaeu-traceroute', 'blaeu-cert'],

)
