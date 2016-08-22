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
from PyQt5.QtCore import Qt, QTimer, QSettings, QSize
from ppeMod import PhoenixClass, PhoenixChecker
from qppe.dialogs import SelectDlg, SettingsDlg, AddDlg, EditDlg
class MainWindow(QMainWindow):
    """Class to display current status of LCPS' StudentVue"""
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("StudentVue")

        # get settings, with a default none on splitter states
        main_splitter_state = selection_splitter_state = None
        self.settings = QSettings('Scott Stewart', 'qPPE')
        if self.settings.value("Settings Dialog/save_state", True):
            if SettingsDlg.str_bool(self.settings.value('Settings Dialog/save_size')): # str_bool is necessary because of anamolies
                self.resize(self.settings.value("main_window/size", QSize(960, 540)))
            else:
                self.resize(QSize(960, 540))
            if SettingsDlg.str_bool(self.settings.value('Settings Dialog/save_pos')) and self.settings.value("main_window/pos"):
                self.move(self.settings.value("main_window/pos"))
            if SettingsDlg.str_bool(self.settings.value('Settings Dialog/save_splitters')) and self.settings.value('main_window/main_splitter'):
                main_splitter_state = self.settings.value('main_window/main_splitter')
                selection_splitter_state = self.settings.value('main_window/selection_splitter')

        self.settings.beginGroup('Settings Dialog')   
        handle = SettingsDlg.str_bool(self.settings.value('handle_ppe'))
        self.exit_on_close = handle and not SettingsDlg.str_bool(self.settings.value('continue_running'))
        if handle:
            phoenix.daemon_exit(quiet=True)

        # make and populate a set of tabs per quarter (updated with classlist)
        self.quarter_tabs = QTabWidget()
        self.grade_tables = [self.gradetable() for i in range(4)]
        self.class_totals = [self.totaltable() for i in range(4)]
        for ind, table in enumerate(self.grade_tables):
            # composed of a table from the list, overtop 'total: ' and a table of totals from the list
            total_layout = QHBoxLayout()
            total_layout.addWidget(QLabel("Total:"))
            total_layout.addWidget(self.class_totals[ind])
            self.class_totals[ind].setFrameStyle(QFrame.Plain)
            total_widget = QWidget()
            total_widget.setLayout(total_layout)
            total_widget.setMaximumHeight(50) 
            overall_layout = QVBoxLayout()
            overall_layout.addWidget(table)
            overall_layout.addWidget(total_widget)
            overall_widget = QWidget()
            overall_widget.setLayout(overall_layout)
            self.quarter_tabs.addTab(overall_widget, 'Q&{}'.format(ind+1))

        # create stack widget to switch between tabs, overview, and label for no classes
        self.stack_widget = QStackedWidget()
        self.overview_table = self.gradetable(header=('Class', 'Q1', 'Q2', 'Q3', 'Q4'))
        self.overview_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stack_widget.addWidget(self.overview_table)
        self.stack_widget.addWidget(self.quarter_tabs)
        empty_label = QLabel("No classes are selected.")
        empty_label.setAlignment(Qt.AlignCenter)
        self.stack_widget.addWidget(empty_label)

        # make lists of accounts (sorted) and classes, updating ui when an item is pressed
        self.account_list = QListWidget()
        self.account_list.setAlternatingRowColors(True)
        self.account_list.itemSelectionChanged.connect(lambda: self.updateui(populate_accounts=False))
        self.account_list.setSortingEnabled(True)
        self.account_list.setVisible(SettingsDlg.str_bool(self.settings.value('view_accounts', True)))
        self.account_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.account_list.customContextMenuRequested.connect(self.accountListMenu)
        self.class_list = QListWidget()
        self.class_list.setAlternatingRowColors(True)
        self.class_list.itemSelectionChanged.connect(lambda: self.updateui(False, False))
        self.class_list.itemPressed.connect(self.updateui)
        
        # create splitter between lists of acocunts and classes, making classes larger (2:1) 
        self.selection_splitter = QSplitter(Qt.Vertical)
        self.selection_splitter.addWidget(self.account_list)
        self.selection_splitter.addWidget(self.class_list)
        if selection_splitter_state:
            self.selection_splitter.restoreState(selection_splitter_state)
        else:
            self.selection_splitter.setStretchFactor(0,1)
            self.selection_splitter.setStretchFactor(1,2)

        # create splitter betweem class/accounts and the middle part (overview/quarter tabs) (1:3)
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.addWidget(self.selection_splitter)
        self.main_splitter.addWidget(self.stack_widget)
        if main_splitter_state:
            self.main_splitter.restoreState(main_splitter_state)
        else:
            self.main_splitter.setStretchFactor(0,2)
            self.main_splitter.setStretchFactor(1,5)
        self.setCentralWidget(self.main_splitter)
        self.quarter_tabs.currentChanged.connect(self.updateui)

        # create actions for use with "file" menu (about, settings, quit)
        about_action = QAction("&About", self)
        about_action.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
        about_action.triggered.connect(lambda: webbrowser.open('https://github.com/scottkstewart/qPPE', new=0, autoraise=True))
        setting_action = QAction("&Settings", self)
        setting_action.setIcon(self.style().standardIcon(QStyle.SP_TitleBarContextHelpButton))
        setting_action.triggered.connect(self.getSettings)
        quit_action = QAction("&Quit", self)
        quit_action.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
        quit_action.triggered.connect(QApplication.instance().quit)
        self.file_actions = (about_action, setting_action, quit_action)

        # create actions for use with "edit" menu for manipulating accout list
        add_action = QAction("A&dd an account", self)
        add_action.setIcon(self.style().standardIcon(QStyle.SP_FileDialogStart))
        add_action.triggered.connect(self.addAccount)
        edit_action = QAction("&Edit current account", self)
        edit_action.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        edit_action.triggered.connect(lambda: self.editAccount(username=None))          # w/o lambda this passed unwanted arg.
        select_action = QAction("Se&lect Account", self)
        select_action.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxQuestion))
        select_action.triggered.connect(self.selectAccount)
        remove_action = QAction("&Remove current account", self)
        remove_action.setIcon(self.style().standardIcon(QStyle.SP_FileDialogEnd))
        remove_action.triggered.connect(self.removeAccount)    
        self.edit_actions = (add_action, edit_action, select_action, remove_action)

        # create file and edit menus populated with previous actions, as well as a central context menu
        self.file_menu = self.menuBar().addMenu("&File")    
        self.file_menu.addActions(self.file_actions)
        self.edit_menu = self.menuBar().addMenu("&Accounts")    
        self.edit_menu.addActions(self.edit_actions)
        
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.addActions(self.file_actions)
        self.separator = QAction(self)
        self.separator.setSeparator(True)
        self.addAction(self.separator)
        self.addActions(self.edit_actions)

        # add status bar
        self.status_label = QLabel(phoenix.status(quiet=True))
        self.status_label.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        self.status_bar = self.statusBar()
        self.status_bar.addPermanentWidget(self.status_label)
   
        # get data from PPE database 
        data = shelve.open('/etc/ppe/data')
        try:
            self.accounts = data['accounts']
        except KeyError:
            self.accounts = data['accounts'] = {}
        data.close()

        # set the tab index to the current quarter (updates ui)
        if self.accounts:
            self.quarter_tabs.setCurrentIndex(list(self.accounts.values())[0].currentQuarter-1)
            if not list(self.accounts.values())[0].currentQuarter-1:
                self.updateui()
        else:
            self.updateui()

        if handle:
            os.system('phoenix start -n')   # fix later
    
    def gradetable(self, header=('Assignment', 'Numerator', 'Denominator', 'Percentage', 'Grade')):
        '''Helper method which constructs and returns a QTableWidget with the specified header, no vertical header, and
           stretched first column'''
        table = QTableWidget(self)
        table.setColumnCount(len(header))
        table.setHorizontalHeaderLabels(header)
        table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch)
        table.verticalHeader().hide()
        table.setAlternatingRowColors(True)
        return table

    def totaltable(self):
        '''Similar to gradetable() for the 4x1, headerless table of totals at the bottom of the tabwidget'''
        table = QTableWidget(self)
        table.setColumnCount(4)
        table.setRowCount(1)
        table.verticalHeader().hide()
        table.horizontalHeader().hide()
        table.setMaximumWidth(402)
        return table

    def accountListMenu(self, pos):
        '''Custom context menu handler for accountList widget'''
        overall_menu = QMenu(self)
        username = self.account_list.currentItem().text() if self.account_list.count() else ''
        hide_action = QAction("&Hide this widget", self)
        hide_action.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMinButton))
        hide_action.triggered.connect(lambda: self.account_list.setVisible(False))
        hide_action.triggered.connect(lambda: self.settings.setValue('view_accounts', False))
        edit_action = QAction("&Edit account {}".format(username), self)
        edit_action.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        edit_action.triggered.connect(lambda: self.editAccount(username))
        remove_action = QAction("&Remove account {}".format(username), self)
        remove_action.setIcon(self.style().standardIcon(QStyle.SP_FileDialogEnd))
        remove_action.triggered.connect(lambda: self.removeAccount(username))    
        overall_menu.addActions((hide_action, edit_action, remove_action, self.separator))
        overall_menu.addMenu(self.file_menu)
        overall_menu.addMenu(self.edit_menu)
        overall_menu.popup(self.account_list.viewport().mapToGlobal(pos))

    def getSettings(self):
        '''Show settings dialog and lock in any changed settings'''
        dlg = SettingsDlg(self)
        if dlg.exec_() and dlg.changes:
            self.status_bar.showMessage("Settings updated ({:04x}).".format(dlg.changes), 5000)
            if dlg.changes & SettingsDlg.ACCOUNTS:
                self.account_list.setVisible(dlg.view_accounts.checkState())
            self.settings.sync()

    def addAccount(self):
        '''Show dialog to add an account to the database, giving a 5s message on the status bar if successful'''
        dlg = AddDlg(self)
        if dlg.exec_():
            self.status_bar.showMessage('Account {} added.'.format(dlg.username.text()), 5000)         
            self.updateui()
    
    def editAccount(self, username=None):
        '''Show dialog to edit the current account, giving a 5s message on the status bar when applied'''
        if not self.account_list.count():
            QMessageBox.warning(self, "No account to edit", 'WARNING: There is no account to edit. Run again with accounts logged.')
            return
        elif username is None:
            username = self.account_list.currentItem().text()
        data = shelve.open('/etc/ppe/data') 
        dlg = EditDlg(self, data['accounts'][username])
        data.close()
        if dlg.exec_():
            self.status_bar.showMessage(dlg.edits, 5000)
            self.updateui()

    def selectAccount(self):
        '''Show dialog to select an account from the list'''
        dlg = SelectDlg(self, self.account_list)
        if not self.account_list.count():
            QMessageBox.warning(self, "No account to select", 'WARNING: There is no account to select. Run again with accounts logged.')
            return
        if dlg.exec_():
            self.status_bar.showMessage('Account {} selected.'.format(dlg.account_box.currentText()), 5000)

    def removeAccount(self, username=None):
        '''Confirm the user wants to delete the current account, then delete it.'''
        if not self.account_list.count():
            QMessageBox.warning(self, "No account to remove", 'WARNING: There is no account to remove. Run again with accounts logged.')
            return
        elif username is None:
            username = self.account_list.currentItem().text()
        if QMessageBox.question(self,
                                'Remove Account',
                                'Are you sure you want to remove account {}?'.format(username),
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            data = shelve.open('/etc/ppe/data', writeback=True)
            del data['accounts'][username]
            data.close()
            self.account_list.takeItem(self.account_list.currentRow())
            self.status_bar.showMessage('Account {} deleted.'.format(username))
            phoenix.log('[{}] Account {} deleted.'.format(str(datetime.datetime.now()), username))
            self.updateui()

    def updateui(self, populate_accounts=True, populate_classes=True):
        '''Updates the ui on state changes, potentially without accountlist population to avoid recursion'''
        # sync accounts with database
        data = shelve.open('/etc/ppe/data')
        self.accounts = data['accounts']
        data.close()

        # set status to whether or not the daemon is running
        self.status_label.setText(phoenix.status(quiet=True))

        # populate accountlist (default to selecting item 0) unless otherwise specified
        ind = self.account_list.currentRow()
        if populate_accounts:
            self.account_list.clear()
            self.account_list.addItems(self.accounts.keys())
            self.account_list.setCurrentRow(ind if ind >= 0 else 0)
      
        # populate classlist if and account is selected, defaulting to 0 for class selection, as well as including an overview option
        ind = self.class_list.currentRow()
        if populate_classes:
            if ind < 0: ind = 0
            self.class_list.clear()
            if self.account_list.currentItem() is not None:
                self.class_list.addItem('OVERVIEW')
                self.class_list.item(0).setTextAlignment(Qt.AlignHCenter)
                self.class_list.addItems((cl.getName() for cl in self.accounts[self.account_list.currentItem().text()].classes))
                self.class_list.setCurrentRow(ind)
        
            # populate main widget
            if self.class_list.currentItem() is not None and ind >= 0:
                # if "OVERVIEW" is selected
                if ind > 0:
                    # set stackedwidget to the tab widget, get the class, and populate the totals table
                    self.stack_widget.setCurrentIndex(1)
                    cl = self.accounts[self.account_list.currentItem().text()].classes[ind-1]
                    ind = self.quarter_tabs.currentIndex()                
                    totals_table = self.class_totals[ind]
                    totals_table.setItem(0, 0, QTableWidgetItem(str(cl.getNumerator()[ind])))                
                    totals_table.setItem(0, 1, QTableWidgetItem(str(cl.getDenominator()[ind])))
                    if cl.getDenominator()[ind]:
                        totals_table.setItem(0, 2, QTableWidgetItem('{:0.1f}%'.format(cl.getNumerator()[ind]/cl.getDenominator()[ind]*100)))
                    else:
                        totals_table.setItem(0, 2, QTableWidgetItem())
                    totals_table.setItem(0, 3, QTableWidgetItem(cl.getGrade()[ind].split(' ')[0]))
                    for i in range(4): 
                        totals_table.item(0,i).setFlags(Qt.ItemIsEnabled) # no select or edit flags
                        totals_table.item(0,i).setTextAlignment(Qt.AlignCenter)

                    # get assignments and populate table of all assignments
                    assignmentList = cl.getAssignments()[ind]
                    table = self.grade_tables[ind]
                    table.setRowCount(len(assignmentList))
                    for row, assignment in enumerate(assignmentList):
                        grade, num, denom = re.split("[/()]",assignment[1])[:3]
                        table.setItem(row, 0, QTableWidgetItem(assignment[0]))
                        table.setItem(row, 1, QTableWidgetItem(num))
                        table.setItem(row, 2, QTableWidgetItem(denom))
                        table.setItem(row, 3, QTableWidgetItem('{:0.1f}%'.format(int(num)/int(denom)*100)))
                        table.setItem(row, 4, QTableWidgetItem(grade[:-1]))
                        table.item(row, 0).setFlags(Qt.ItemIsEnabled) # no select or edit flags
                        for i in range(1, 5):
                            table.item(row, i).setFlags(Qt.ItemIsEnabled)
                            table.item(row, i).setTextAlignment(Qt.AlignCenter)

                else: #if a class is selected
                    # set stackedwidget to the overview widget, get classes, and populate with a per-quarter overview of each class
                    self.stack_widget.setCurrentIndex(0)
                    classes = self.accounts[self.account_list.currentItem().text()].classes
                    self.overview_table.setRowCount(len(classes))
                    for row, cl in enumerate(classes):
                        self.overview_table.setItem(row, 0, QTableWidgetItem(cl.getName()))
                        self.overview_table.item(row, 0).setFlags(Qt.ItemIsEnabled)
                        for q in range(4):
                            self.overview_table.setItem(row, q+1, QTableWidgetItem('{} ({}/{})'.format(cl.getGrade()[q], str(cl.getNumerator()[q]), str(cl.getDenominator()[q])))) 
                            self.overview_table.item(row, q+1).setFlags(Qt.ItemIsEnabled) # no select or edit flags
                            self.overview_table.item(row, q+1).setTextAlignment(Qt.AlignCenter)
            else: # just clear the table if there are no classes selected
                self.stack_widget.setCurrentIndex(2)

    def closeEvent(self, event):
        '''On close, save size and position of the window and exit daemon if necessary'''
        self.settings.endGroup()

        self.settings.beginGroup("main_window")
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        self.settings.setValue("main_splitter", self.main_splitter.saveState())
        self.settings.setValue("selection_splitter", self.selection_splitter.saveState())
        self.settings.endGroup()

        if self.exit_on_close:
            phoenix.daemon_exit()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = MainWindow()
    form.show()
    sys.exit(app.exec_())
