#!/usr/bin/env python3
import os
from distutils.core import setup
setup(name='qPPE',
      description='QT-Phoenix-Parse-Email',
      author='Scott Stewart',
      url='https://github.com/scottkstewart/qPPE',
      author_email='scottkstewart16@gmail.com',
      requires=['pyqt5', 'ppeMod', 'phoenix'],
      packages=['qppe'])
os.system('cp run.pyw /usr/bin/qPPE')
