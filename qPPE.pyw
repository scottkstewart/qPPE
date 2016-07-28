#!/usr/bin/env python3
import sys
import re
import shelve
import webbrowser
import phoenix
from PyQt5.QtWidgets import (QMainWindow, QApplication, QListWidget, QDockWidget, QVBoxLayout, QWidget, QAction, QStyle, QFrame, QLabel, QTableWidget, QHeaderView, QTableWidgetItem, QSplitter, QTabWidget, QStackedWidget, QHBoxLayout, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt
from ppeMod import (phoenixClass, phoenixChecker)

__version__ = "1.0.0"

class TestPC(phoenixChecker):
    """Stub-filled class for testing during the summer"""
    def updatePage(self):
        pass
    def update(self):
        pass
    def urlUpdatae(self):
        pass
    def __init__(self, user, password, email, classes=phoenixClass(None, 'Default')):    
        self.classes = [cl for cl in classes]
        self.username='filler'

class MainWindow(QMainWindow):
    """Class to display current status of LCPS' StudentVue"""
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("StudentVue")

        # make and populate a set of tabs per quarter (updated with classlist)
        self.quarter_tabs = QTabWidget()
        self.grade_tables = [self.gradetable() for i in range(4)]
        self.class_totals = [self.totaltable() for i in range(4)]
        for ind, table in enumerate(self.grade_tables):
            # composed of a table from the list, overtop 'total: ' and a table of totals from the list
            total_layout = QHBoxLayout()
            total_layout.addWidget(QLabel("Total:"))
            total_layout.addWidget(self.class_totals[ind])
            total_widget = QWidget()
            total_widget.setLayout(total_layout)
            total_widget.setMaximumHeight(50) 
            overall_layout = QVBoxLayout()
            overall_layout.addWidget(table)
            overall_layout.addWidget(total_widget)
            overall_widget = QWidget()
            overall_widget.setLayout(overall_layout)
            self.quarter_tabs.addTab(overall_widget, 'Q&{}'.format(ind+1))

        # create stack widget to switch between tabs and overview
        self.stack_widget = QStackedWidget()
        self.overview_table = self.gradetable(header=('Class', 'Q1', 'Q2', 'Q3', 'Q4'))
        self.overview_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stack_widget.addWidget(self.overview_table)
        self.stack_widget.addWidget(self.quarter_tabs)

        # make listss of accounts (sorted) and classes, updating ui when an item is pressed
        self.account_list = QListWidget()
        self.account_list.setAlternatingRowColors(True)
        self.account_list.itemPressed.connect(self.updateui)
        self.account_list.setSortingEnabled(True)
        self.class_list = QListWidget()
        self.class_list.setAlternatingRowColors(True)
        self.class_list.itemPressed.connect(self.updateui)
        
        # create splitter between lists of acocunts and classes, making classes larger (2:1) 
        selection_splitter = QSplitter(Qt.Vertical)
        selection_splitter.addWidget(self.account_list)
        selection_splitter.addWidget(self.class_list)
        selection_splitter.setStretchFactor(0,1)
        selection_splitter.setStretchFactor(1,2)

        # create splitter betweem class/accounts and the middle part (overview/quarter tabs) (1:3)
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(selection_splitter)
        main_splitter.addWidget(self.stack_widget)
        main_splitter.setStretchFactor(0,1)
        main_splitter.setStretchFactor(1,3)
        self.setCentralWidget(main_splitter)
        self.quarter_tabs.currentChanged.connect(self.updateui)

        # create actions for use with "file" menu (about, settings, quit)
        about_action = QAction("&About", self)
        about_action.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
        about_action.triggered.connect(lambda: webbrowser.open('https://github.com/scottkstewart/qPPE', new=0, autoraise=True))
        setting_action = QAction("&Settings", self)
        setting_action.setIcon(self.style().standardIcon(QStyle.SP_TitleBarContextHelpButton))
        quit_action = QAction("&Quit", self)
        quit_action.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
        quit_action.triggered.connect(QApplication.instance().quit)

        # create actions for use with "edit" menu for manipulating accout list
        add_action = QAction("&Add an account", self)
        add_action.setIcon(self.style().standardIcon(QStyle.SP_FileDialogStart))
        edit_action = QAction("&Edit current account", self)
        edit_action.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        remove_action = QAction("&Remove current account", self)
        remove_action.setIcon(self.style().standardIcon(QStyle.SP_FileDialogEnd))

        # create file and edit menus populated with previous actions
        file_menu = self.menuBar().addMenu("&File")    
        file_menu.addActions((about_action, setting_action, quit_action))
        edit_menu = self.menuBar().addMenu("&Accounts")    
        edit_menu.addActions((add_action, edit_action, remove_action))

        # add status bar and show placeholder message
        self.status_label = QLabel(phoenix.status(quiet=True))
        self.status_label.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        status = self.statusBar()
        status.addPermanentWidget(self.status_label)
        status.showMessage("Message here for 5 seconds", 5000) 
   
        # get data from PPE database 
        data = shelve.open('/etc/ppe/data')
        self.accounts = data['accounts']
        data.close()

        # placeholder data for testing during summer
        nl = ('AP Economics', 'AP Statistics', 'AP Government', 'AP Physics C: Mechanics', 'English 12 DE', 'Independent Science Research', 'Geospacial Science DE')
        for i in range(0,10):
            self.accounts['{:06d}'.format(i*111111)] = TestPC('{:06d}'.format(i*111111), 'password', 'test@email.com', (phoenixClass(None, '({}) {}'.format(i, a)) for a in nl))
            self.accounts['{:06d}'.format(i*111111)].currentQuarter = 3            

        for account in self.accounts.values():
            for pClass in account.classes:
                pClass.setAssignments([[('({} Q{}) Assignment #{}.'.format(pClass.getName(), j+1, i+1), 'G ({}/100)'.format(100-i)) for i in range(15)] for j in range(4)])
                pClass.setNumerator([1395, 1395, 1395, 1395])
                pClass.setDenominator([1500,1500,1500,1500])
                pClass.grade = ['A (93)', 'A (93)', 'A (93)', 'A (93)']

        # set the tab index to the current quarter (updates ui)
        self.quarter_tabs.setCurrentIndex(list(self.accounts.values())[0].currentQuarter-1)

    
    def gradetable(self, header=('Assignment', 'Numerator', 'Denominator', 'Percentage', 'Grade')):
        '''Helper method which constructs and returns a QTableWidget with the specified header, no vertical header, and
           stretched first column
        '''
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

    def updateui(self):
        '''Updates the ui on state changes'''
        # set status to whether or not the daemon is running
        self.status_label.setText(phoenix.status(quiet=True))

        # populate accountlist (default to selecting item 0)
        ind = self.account_list.currentRow()
        self.account_list.clear()
        self.account_list.addItems(self.accounts.keys())
        self.account_list.setCurrentRow(ind if ind >= 0 else 0)
      
        # populate classlist if and account is selected, defaulting to 0 for class selection, as well as including an overview option
        ind = self.class_list.currentRow()
        if ind < 0: ind = 0
        self.class_list.clear()
        if self.account_list.currentItem() is not None:
            self.class_list.addItem('OVERVIEW')
            self.class_list.addItems((cl.getName() for cl in self.accounts[self.account_list.currentItem().text()].classes))
            self.class_list.setCurrentRow(ind)
        
        # populate main widget
        if self.class_list.currentItem() is not None:
            # if "OVERVIEW" is selected
            if ind > 0:
                # set stackedwidget to the tab widget, get the class, and populate the totals table
                self.stack_widget.setCurrentIndex(1)
                cl = self.accounts[self.account_list.currentItem().text()].classes[ind-1]
                ind = self.quarter_tabs.currentIndex()                
                totals_table = self.class_totals[ind]
                totals_table.setItem(0, 0, QTableWidgetItem(str(cl.getNumerator()[ind])))                
                totals_table.setItem(0, 1, QTableWidgetItem(str(cl.getDenominator()[ind])))
                totals_table.setItem(0, 2, QTableWidgetItem('{:0.1f}%'.format(cl.getNumerator()[ind]/cl.getDenominator()[ind]*100)))
                totals_table.setItem(0, 3, QTableWidgetItem(cl.getGrade()[ind].split(' ')[0]))
                for i in range(4): totals_table.item(0,i).setFlags(Qt.ItemIsEnabled) # no select or edit flags
                
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
                    for i in range(5): table.item(row, i).setFlags(Qt.ItemIsEnabled) # no select or edit flags
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = MainWindow()
    form.resize(960,540)
    form.show()
    sys.exit(app.exec_())
