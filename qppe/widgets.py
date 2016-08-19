#!/usr/bin/env python3
import sys
import re
from PyQt5.QtWidgets import QSpinBox, QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QRegExpValidator
class TimeSpinBox(QSpinBox):
    """Custom widget to collect an interval in time, used primarily in the settings dialog"""
    SUFFIXES = {'s': 1, 'm':60, 'h':60*60, 'd':60*60*24}
    
    def __init__(self, parent=None, time=900):
        super(TimeSpinBox, self).__init__(parent)
        self.validator = QRegExpValidator(QRegExp(r'(\d+\s*[{}]\s*)+'.format(''.join([key for key in self.SUFFIXES.keys()]), Qt.CaseInsensitive))) 
        self.setMaximum(60*60*24*7 - 1)
        self.setValue(time)

    def validate(self, text, pos):
        '''Overriden validation alidate using regex'''
        return self.validator.validate(text, pos)

    def textFromValue(self, value):
        '''Overriden method to get the line edit's text from a value in seconds'''
        text = ''
        # add a #s entry to the text per suffix
        for suffix in sorted(self.SUFFIXES):
            if value >= self.SUFFIXES[suffix]:
                text += '{}{}{}'.format('' if text == '' else ' ', value//self.SUFFIXES[suffix], suffix)
                value %= self.SUFFIXES[suffix]
            elif text != '':
                text += ' 0{}'.format(suffix)
        return text

    def valueFromText(self, value):
        '''Overriden method to get the value in seconds from the line edit's text'''
        num = 0
        # get the number of each extension and multiply by their value in SUFFIXES
        for suffix in self.SUFFIXES:
            entry = re.search(r"(\d+)\s*{}".format(suffix), value)
            if entry:
                num += int(entry.group(1))*self.SUFFIXES[suffix]
        return num
