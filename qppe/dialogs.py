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
from PyQt5.QtCore import Qt, QTimer, QSettings, QRegExp
from PyQt5.QtGui import QRegExpValidator
from ppeMod import PhoenixClass, PhoenixChecker
from qppe.widgets import TimeSpinBox

class SettingsDlg(QDialog):
    """Dialog for manipulating settings for display and PPE settings"""
    INTERVAL =  0x0001
    AUTOTRY =   0x0002
    HANDLE =    0x0004
    EMAIL =     0x0008
    CONTINUE =  0x0010
    ACCOUNTS =  0x0020
    STATE =     0x0040
    SIZE =      0x0080
    POS =       0x0100
    SPLITTERS = 0x0200

    # lambda for whether a setting is actually a string and true (happens automatically with QSettings)
    str_bool = lambda val: bool(val) and (not isinstance(val, str) or (isinstance(val, str) and val != 'false'))
    
    def __init__(self, parent=None):
        super(SettingsDlg, self).__init__(parent)
        self.setWindowTitle("Settings")
        overall_layout = QVBoxLayout()
        self.setLayout(overall_layout)

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

        # make tabwidget divided between general and view settings
        tab_widget = QTabWidget()
        overall_layout.addWidget(tab_widget)
        general_widget = QWidget()
        view_widget = QWidget()
        general_layout = QGridLayout()
        general_widget.setLayout(general_layout)
        view_layout = QGridLayout()
        view_widget.setLayout(view_layout)
        tab_widget.addTab(general_widget, "&General")
        tab_widget.addTab(view_widget, "&View")

        # check interval is combo/spinbox for type (sec, min) and number of sec/mins, keeping the two consistent and updated w/ a variable for secs
        interval_label = QLabel("&Check interval:")
        self.interval = TimeSpinBox(self, interval)
        interval_label.setBuddy(self.interval)
        general_layout.addWidget(interval_label, 0, 0)
        general_layout.addWidget(self.interval, 0, 1)
    
        # do autotry the same as check interval
        autotry_label = QLabel("&Autotry interval:")
        self.autotry = TimeSpinBox(self, autotry)
        autotry_label.setBuddy(self.autotry)
        general_layout.addWidget(autotry_label, 1, 0)
        general_layout.addWidget(self.autotry, 1, 1)

        # checkbox on whether to check email, uses setting if available,controls visibility of subsequent settings
        self.handle_ppe = self.constructCheckBox("Automatically &handle scheduling checks?", "handle_ppe", True)
        general_layout.addWidget(self.handle_ppe, 2, 0, 1, 2)

        # checkbox on whether to send emails if PPE is being handled by the app or should be closed on exit, usability dependent on handle_ppe
        self.send_emails = self.constructCheckBox("&Send email notifiations?", "send_emails", False)
        self.continue_running = self.constructCheckBox("Continue &running PPE after close?", "continue_running", True)
        
        # frame holding options dependent on handling
        handle_widgets = QFrame()
        handle_layout = QVBoxLayout()
        handle_widgets.setLayout(handle_layout)
        handle_widgets.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        handle_layout.addWidget(self.send_emails)
        handle_layout.addWidget(self.continue_running)
        self.handle_ppe.stateChanged.connect(lambda state: handle_widgets.setCheckState(state))
        general_layout.addWidget(handle_widgets, 3, 0, 2, 2)

        # checkbox on whether to keep account selection visible on main window
        self.view_accounts = self.constructCheckBox("&Show account choices?", "view_accounts", True)
        view_layout.addWidget(self.view_accounts, 0, 0)
        
        # checkbox on whether to save application state
        self.save_state = self.constructCheckBox("Save &application state?", "save_state", True)
        view_layout.addWidget(self.save_state, 1, 0)

        # checkboxes on whther to save size, powition, splitters, etc, contingent on save_state
        self.save_size = self.constructCheckBox("Save &window size?", "save_size", True)
        self.save_pos = self.constructCheckBox("Save window &position?", "save_pos", True)
        self.save_splitters = self.constructCheckBox("Save window &geometry?", "save_splitters", False)

        # frame holding options dependent on handling
        state_widgets = QFrame()
        state_layout = QVBoxLayout()
        state_widgets.setLayout(state_layout)
        state_widgets.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        state_layout.addWidget(self.save_size)
        state_layout.addWidget(self.save_pos)
        state_layout.addWidget(self.save_splitters)
        self.save_state.stateChanged.connect(lambda state: state_widgets.setEnabled(state))
        view_layout.addWidget(state_widgets, 2, 0, 3, 1)

        view_layout.setRowStretch(5, 1)
        # ok/cancel buttons on custom accept
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        overall_layout.addWidget(buttons)
    
    def constructCheckBox(self, text, setting_text, default):
        box = QCheckBox(text)
        setting = self.settings.value(setting_text)
        if setting is not None:
            box.setCheckState(SettingsDlg.str_bool(setting))
        else:
            box.setCheckState(default)
            self.settings.setValue(setting_text, default)
        box.setTristate(False)
        return box

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
        if self.save_state.isChecked() != SettingsDlg.str_bool(self.settings.value('save_state')):
            self.settings.setValue('save_state', self.save_state.isChecked())
            self.changes |= self.STATE
        if self.save_size.isChecked() != SettingsDlg.str_bool(self.settings.value('save_size')):
            self.settings.setValue('save_size', self.save_size.isChecked())
            self.changes |= self.SIZE
        if self.save_pos.isChecked() != SettingsDlg.str_bool(self.settings.value('save_pos')):
            self.settings.setValue('save_pos', self.save_pos.isChecked())
            self.changes |= self.POS
        if self.save_splitters.isChecked() != SettingsDlg.str_bool(self.settings.value('save_splitters')):
            self.settings.setValue('save_splitters', self.save_splitters.isChecked())
            self.changes |= self.SPLITTERS
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
        self.email.setValidator(QRegExpValidator(QRegExp(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", Qt.CaseInsensitive)))
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
    '''Dialog to select an account fom all logged accounts (same as accountlist)'''
    def __init__(self, parent, accounts):
        '''Just a simple label and combo box'''
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
        '''Update the accountlist and exit'''
        self.account_list.setCurrentRow(self.account_box.currentIndex())
        QDialog.accept(self)
