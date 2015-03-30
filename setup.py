try:
  from setuptools import setup
except ImportError:
  from distutils.core import setup

  config = {
    'description': 'Stats Lifesum',
    'author': 'Carlos Mateos',
    'url': 'github.com/lifestats',
    'author_email': 'wuiscmc@gmail.com',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['lifestats'],
    'scripts': [],
    'name': 'lifestats'
  }

  setup(**config)

