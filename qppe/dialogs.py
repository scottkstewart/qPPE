#!/usr/bin/env python3
import sys
import os
import re
import shelve
import webbrowser
import phoenix
import datetime
import signal
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, QSettings
from ppeMod import PhoenixClass, PhoenixChecker
from qppe.widgets import TimeSpinBox

class SettingsDlg(QDialog):
    """Dialog for manipulating settings for display and PPE settings"""
    CUTOFFS = (1, 60, 60*60, 60*60*24) 
    INTERVAL = 0x01
    AUTOTRY = 0x02
    HANDLE = 0x04
    EMAIL = 0x08
    CONTINUE = 0x10
    ACCOUNTS = 0x20

    # lambda for whether a setting is actually a string and true (happens automatically with QSettings)
    str_bool = lambda val: bool(val) and (not isinstance(val, str) or (isinstance(val, str) and val != 'false'))
    
    def __init__(self, parent=None):
        super(SettingsDlg, self).__init__(parent)
        self.setWindowTitle("Settings")
        grid = QGridLayout()
        self.setLayout(grid)

        # get relevant data to populate settings panel
        data = shelve.open('/etc/ppe/data')
        interval = autotry = 900
        try:
            interval = data['interval']
            autotry = data['autotry']
        except KeyError:
            pass
        data.close()

        self.settings = QSettings("Scott Stewart", "qPPE")
        self.settings.beginGroup("Settings Dialog")

        # check interval is combo/spinbox for type (sec, min) and number of sec/mins, keeping the two consistent and updated w/ a variable for secs
        interval_label = QLabel("&Check interval:")
        self.interval = TimeSpinBox(self, interval)
        interval_label.setBuddy(self.interval)
        grid.addWidget(interval_label, 0, 0)
        grid.addWidget(self.interval, 0, 1)
    
        # do autotry the same as check interval
        autotry_label = QLabel("&Autotry interval:")
        self.autotry = TimeSpinBox(self, autotry)
        autotry_label.setBuddy(self.autotry)
        grid.addWidget(autotry_label, 1, 0)
        grid.addWidget(self.autotry, 1, 1)

        # checkbox on whether to keep account selection visible on main window
        self.view_accounts = QCheckBox("&Show account choices?")
        view_setting = self.settings.value('view_accounts')
        if view_setting is not None:
            # on initial opening, boolean settings are actually lowercase string equivalents
            self.view_accounts.setCheckState(SettingsDlg.str_bool(view_setting))
        else:
            self.view_accounts.setCheckState(True)
            self.settings.setValue('view_accounts', True)
        self.view_accounts.setTristate(False)
        grid.addWidget(self.view_accounts, 2, 0, 1, 2)

        # checkbox on whether to check email, uses setting if available,controls visibility of subsequent settings
        self.handle_ppe = QCheckBox("Automatically &handle scheduling checks?")
        handle_setting = self.settings.value('handle_ppe')
        if handle_setting is not None:
            self.handle_ppe.setCheckState(SettingsDlg.str_bool(handle_setting))
        self.handle_ppe.setTristate(False)
        grid.addWidget(self.handle_ppe, 3, 0, 1, 2)

        # checkbox on whether to send emails if PPE is being handled by the app or should be closed on exit, usability dependent on handle_ppe
        self.send_emails = QCheckBox("&Send email notifiations?")
        self.send_emails.setEnabled(self.handle_ppe.checkState())
        email_setting = self.settings.value('send_emails')
        if email_setting is not None:
            self.send_emails.setCheckState(SettingsDlg.str_bool(email_setting))
        self.send_emails.setTristate(False)
        self.handle_ppe.stateChanged.connect(lambda: self.send_emails.setEnabled(self.handle_ppe.checkState()))

        self.continue_running = QCheckBox("&Continue running PPE after close?")
        self.continue_running.setEnabled(self.handle_ppe.checkState())
        continue_setting = self.settings.value('continue_running')
        if continue_setting is not None:
            self.continue_running.setCheckState(SettingsDlg.str_bool(continue_setting))
        self.continue_running.setTristate(False)
        self.handle_ppe.stateChanged.connect(lambda: self.continue_running.setEnabled(self.handle_ppe.checkState()))
        
        # frame holding options dependent on handling
        handle_widgets = QFrame()
        handle_layout = QVBoxLayout()
        handle_widgets.setLayout(handle_layout)
        handle_widgets.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        handle_layout.addWidget(self.send_emails)
        handle_layout.addWidget(self.continue_running)
        grid.addWidget(handle_widgets, 4, 0, 2, 2)

        # ok/cancel buttons on custom accept
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        grid.addWidget(buttons, 6, 0, 1, 2)

        # set fixed size (for expansion dialog)
        grid.setSizeConstraint(QLayout.SetFixedSize)
    
    def accept(self):
        '''Updates a bitmask for changes since the beginning of the dialog and closes the dialog'''
        self.changes = 0

        data = shelve.open('/etc/ppe/data')
        if not 'interval' in data or self.interval.value() != data['interval']:
            data['interval'] = self.interval.value()
            self.changes |= self.INTERVAL
        if not 'autotry' in data or self.autotry.value() != data['autotry']:
            data['autotry'] = self.autotry.value()
            self.changes |= self.AUTOTRY
        data.close()
        
        if self.handle_ppe.isChecked() != SettingsDlg.str_bool(self.settings.value('handle_ppe')):
            self.settings.setValue('handle_ppe', self.handle_ppe.isChecked())
            self.changes |= self.HANDLE
        if self.send_emails.isChecked() != SettingsDlg.str_bool(self.settings.value('send_emails')):
            self.settings.setValue('send_emails', self.send_emails.isChecked())
            self.changes |= self.EMAIL
        if self.continue_running.isChecked() != SettingsDlg.str_bool(self.settings.value('continue_running')):
            self.settings.setValue('continue_running', self.continue_running.isChecked())
            self.changes |= self.CONTINUE
        if self.view_accounts.isChecked() != SettingsDlg.str_bool(self.settings.value('view_accounts')):
            self.settings.setValue('view_accounts', self.view_accounts.isChecked())
            self.changes |= self.ACCOUNTS
        self.settings.sync()
        self.settings.endGroup()

        QDialog.accept(self)

class AccountDlg(QDialog):
    """Skeleton for account-action dialogs, doesn't include username or custom accept()"""
    def __init__(self, parent=None, title="Account Action"):
        # leave space open for custom username display
        super(AccountDlg, self).__init__(parent)
        self.setWindowTitle(title)
        self.grid = QGridLayout() 
        self.setLayout(self.grid)

        # password label/text box which defaults to password-style echo
        password_label = QLabel("&Password:")
        self.password = QLineEdit()
        password_label.setBuddy(self.password)
        self.password.setEchoMode(QLineEdit.Password)
        self.grid.addWidget(password_label, 1, 0)
        self.grid.addWidget(self.password, 1, 1) 

        # checkbox to show password when clicked
        self.show_password = QCheckBox("&Show Password")
        self.show_password.stateChanged.connect(lambda: self.password.setEchoMode(QLineEdit.Normal if self.show_password.checkState() else QLineEdit.Password))
        self.grid.addWidget(self.show_password, 2, 0, 1, 2)

        # email label/text box with normal echo
        email_label = QLabel("&Email:")
        self.email = QLineEdit()
        email_label.setBuddy(self.email)
        self.grid.addWidget(email_label, 3, 0)
        self.grid.addWidget(self.email, 3, 1)

        # red error label, only visible after bad login
        self.error_label = QLabel("<font color=red>Bot invalid, no grades found.</font>")
        self.error_label.setVisible(False)
        self.grid.addWidget(self.error_label, 4, 0, 1, 2)

        # ok/cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        self.grid.addWidget(buttons, 5, 0, 1, 2)

class AddDlg(AccountDlg):
    """Dialog for adding accounts to be displayed"""
    def __init__(self, parent=None):
        '''Add username line-edit in the whole left in the super's grid, and focus when available'''
        super(AddDlg, self).__init__(parent, "Add Account")
        self.username = QLineEdit()
        username_label = QLabel("&Username:")
        username_label.setBuddy(self.username)
        self.grid.addWidget(username_label, 0, 0)
        self.grid.addWidget(self.username, 0, 1) 
        QTimer.singleShot(0, self.username.setFocus)
    
    def accept(self):
        '''Validates and logs the bots, closing the dialog if successful but displaying an error and allowing retries if
           unsuccessful'''    
        username = self.username.text()
        try:
            bot = PhoenixChecker(username, self.password.text(), self.email.text())
        except IndexError:                      # index error is typical of an incorrect password in PPE
            self.error_label.setVisible(True)
        else:
            data = shelve.open('/etc/ppe/data')
            # open messagebox to double check overwrite if the bot already exists
            if not username in data['accounts'].keys() or QMessageBox.question(self,
                                                                "Overwrite?", 
                                                                "Are you sure you want to overwrite bot {}?".format(username), 
                                                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                data['accounts'][username] = bot
                phoenix.log('[{}] {} added to database.'.format(str(datetime.datetime.now()), username))
               
            data.close()
            QDialog.accept(self)

class EditDlg(AccountDlg):
    """Dialog for editing accounts to be displayed (mostly email since password changes are problematic)"""
    def __init__(self, parent=None, account=None):
        self.account = account
        
        # Fill hole in super's grid with labels
        super(EditDlg, self).__init__(parent, "Edit Account")
        username_title = QLabel("Username: ")
        username_label = QLabel(self.account.username)
        self.grid.addWidget(username_title, 0, 0)
        self.grid.addWidget(username_label, 0, 1)

        # Populate email field
        self.email.setText(self.account.email)

    def accept(self):
        '''Adds changes to bot if there are any, validating changed passwords'''
        username = self.account.username
        email = self.account.email
        if self.password.text() != self.account.password:
            try:
                bot = PhoenixChecker(username, self.password.text(), email)
            except IndexError:                  # index error is typical of an incorrect password in PPE
                self.error_label.setVisible(True)
            else:
                # if the password is changed successfully, log edit (email if changed) and accept
                self.edits = "{}'s password {}changed.".format(username, '' if self.email.text() == email else 'and email ')
                data=shelve.open('/etc/ppe/data')
                data['accounts'][username] = bot
                data.close()
                phoenix.log('[{}] {}'.format(str(datetime.datetime.now()), self.edits))
                QDialog.accept(self)
        elif self.email.text() != email:
            # if only email is changed, validate, log, and accept
            self.account.email = email
            self.edits = "{}'s email changed".format(username)
            data=shelve.open('/etc/ppe/data')
            data['accounts'][username] = self.account
            data.close()
            phoenix.log('[{}] {}'.format(str(datetime.datetime.now()), self.edits))
            QDialog.accept(self)
        else:
            # if it's the same, exit with a message about nothing being edited
            self.edits = "No edits made on {}".format(username)
            QDialog.accept(self)

class SelectDlg(QDialog):
    def __init__(self, parent, accounts):
        super(SelectDlg, self).__init__(parent)
        self.account_list = accounts
        self.setWindowTitle("Select Account")
        layout = QHBoxLayout()
        temp = QWidget()
        temp.setLayout(layout)
        overall_layout = QVBoxLayout()
        overall_layout.addWidget(temp)
        self.setLayout(overall_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        overall_layout.addWidget(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(QLabel("Selected Account:"))
        self.account_box = QComboBox()
        self.account_box.addItems([self.account_list.item(i).text() for i in range(self.account_list.count())])
        self.account_box.setCurrentIndex(self.account_list.currentRow())
        layout.addWidget(self.account_box)

    def accept(self):
        self.account_list.setCurrentRow(self.account_box.currentIndex())
        QDialog.accept(self)
