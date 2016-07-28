import os
from distutils.core import setup
setup(name='qPPE',
      version='1.0',
      description='QT-Phoenix-Parse-Email',
      author='Scott Stewart',
      author_email='scottkstewart16@gmail.com',
      requires=['pyqt5', 'ppeMod', 'phoenix'])
os.system('cp qPPE.pyw /usr/bin/qPPE')
