#!/usr/bin/env python3
import sys
import re
import shelve
import webbrowser
from PyQt5.QtWidgets import (QMainWindow, QApplication, QListWidget, QDockWidget, QVBoxLayout, QWidget, QAction, QStyle, QFrame, QLabel, QTableWidget, QHeaderView, QTableWidgetItem, QSplitter, QTabWidget, QStackedWidget)
from PyQt5.QtCore import Qt
from ppeMod import (phoenixClass, phoenixChecker)

__version__ = "1.0.0"

class TestPC(phoenixChecker):
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

        self.tabwidget = QTabWidget()
        self.gradetables = [self.gradetable() for i in range(4)]
        for ind, table in enumerate(self.gradetables):
           self.tabwidget.addTab(table, 'Q&{}'.format(ind+1))

        self.stackwidget = QStackedWidget()
        self.accountOverview = self.gradetable(header=('Class', 'Q1', 'Q2', 'Q3', 'Q4'))
        self.stackwidget.addWidget(self.accountOverview)
        self.stackwidget.addWidget(self.tabwidget)

        self.accountlist = QListWidget()
        self.accountlist.setAlternatingRowColors(True)
        self.accountlist.itemPressed.connect(self.updateui)
        self.accountlist.setSortingEnabled(True)
        self.classlist = QListWidget()
        self.classlist.setAlternatingRowColors(True)
        self.classlist.itemPressed.connect(self.updateui)
        
        self.selectionSplitter = QSplitter(Qt.Vertical)
        self.selectionSplitter.addWidget(self.accountlist)
        self.selectionSplitter.addWidget(self.classlist)
        self.selectionSplitter.setStretchFactor(0,1)
        self.selectionSplitter.setStretchFactor(1,2)

        self.mainSplitter = QSplitter(Qt.Horizontal)
        self.mainSplitter.addWidget(self.selectionSplitter)
        self.mainSplitter.addWidget(self.stackwidget)
        self.mainSplitter.setStretchFactor(0,1)
        self.mainSplitter.setStretchFactor(1,3)
        self.setCentralWidget(self.mainSplitter)
        self.tabwidget.currentChanged.connect(self.updateui)

        aboutAction = QAction("&About", self)
        aboutAction.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
        aboutAction.triggered.connect(lambda: webbrowser.open('https://github.com/scottkstewart/qPPE', new=0, autoraise=True))
        settingsAction = QAction("&Settings", self)
        settingsAction.setIcon(self.style().standardIcon(QStyle.SP_TitleBarContextHelpButton))
        quitAction = QAction("&Quit", self)
        quitAction.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
        quitAction.triggered.connect(QApplication.instance().quit)

        addAction = QAction("&Add an account", self)
        addAction.setIcon(self.style().standardIcon(QStyle.SP_FileDialogStart))
        editAction = QAction("&Edit current account", self)
        editAction.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        removeAction = QAction("&Remove current account", self)
        removeAction.setIcon(self.style().standardIcon(QStyle.SP_FileDialogEnd))

        fileMenu = self.menuBar().addMenu("&File")    
        fileMenu.addActions((aboutAction, settingsAction, quitAction))
        editMenu = self.menuBar().addMenu("&Accounts")    
        editMenu.addActions((addAction, editAction, removeAction))

        self.statusLabel = QLabel("Running")
        self.statusLabel.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        status = self.statusBar()
        status.addPermanentWidget(self.statusLabel)
        status.showMessage("Message here for 5 seconds", 5000) 
    
        data = shelve.open('/etc/ppe/data')
        self.accounts = data['accounts']
        data.close()

        nl = ('AP Economics', 'AP Statistics', 'AP Government', 'AP Physics C: Mechanics', 'English 12 DE', 'Independent Science Research', 'Geospacial Science DE')
        for i in range(0,10):
            self.accounts['{:06d}'.format(i*111111)] = TestPC('{:06d}'.format(i*111111), 'password', 'test@email.com', (phoenixClass(None, '({}) {}'.format(i, a)) for a in nl))

        for key in self.accounts.keys():
            for cl in self.accounts[key].classes:
                cl.setAssignments([[('({} Q{}) Assignment #{}.'.format(cl.getName(), j+1, i+1), 'G ({}/100)'.format(100-i)) for i in range(15)] for j in range(4)])
                cl.setNumerator([1395, 1395, 1395, 1395])
                cl.setDenominator([1500,1500,1500,1500])
                cl.grade = ['A (93)', 'A (93)', 'A (93)', 'A (93)']

        self.updateui()

    def gradetable(self, header=('Assignment', 'Numerator', 'Denominator', 'Percentage', 'Grade')):
        table = QTableWidget(self)
        table.setColumnCount(len(header))
        table.setHorizontalHeaderLabels(header)
        table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch)
        table.setAlternatingRowColors(True)
        return table

    def updateui(self):
        ind = self.accountlist.currentRow()
        self.accountlist.clear()
        self.accountlist.addItems(self.accounts.keys())
        self.accountlist.setCurrentRow(ind if ind >= 0 else 0)
      
        ind = self.classlist.currentRow()
        if ind < 0: ind = 0
        self.classlist.clear()
        if self.accountlist.currentItem() is not None:
            self.classlist.addItem('OVERVIEW')
            self.classlist.addItems((cl.getName() for cl in self.accounts[self.accountlist.currentItem().text()].classes))
            self.classlist.setCurrentRow(ind)
        
        if self.classlist.currentItem() is not None:
            if ind > 0:
                self.stackwidget.setCurrentIndex(1)
                assignmentList = self.accounts[self.accountlist.currentItem().text()].classes[ind-1].getAssignments()[self.tabwidget.currentIndex()]
                table = self.tabwidget.currentWidget()
                table.setRowCount(len(assignmentList))
                for row, assignment in enumerate(assignmentList):
                    grade, num, denom = re.split("[/()]",assignment[1])[:3]
                    table.setItem(row, 0, QTableWidgetItem(assignment[0]))
                    table.setItem(row, 1, QTableWidgetItem(num))
                    table.setItem(row, 2, QTableWidgetItem(denom))
                    table.setItem(row, 3, QTableWidgetItem('{:0.1f}%'.format(int(num)/int(denom)*100)))
                    table.setItem(row, 4, QTableWidgetItem(grade[:-1]))
                    for i in range(0, 5): table.item(row, i).setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable) 
            else:
                self.stackwidget.setCurrentIndex(0)
                classes = self.accounts[self.accountlist.currentItem().text()].classes
                self.accountOverview.setRowCount(len(classes))
                for row, cl in enumerate(classes):
                    self.accountOverview.setItem(row, 0, QTableWidgetItem(cl.getName()))
                    for q in range(4):
                        self.accountOverview.setItem(row, q+1, QTableWidgetItem('{} ({}/{})'.format(cl.getGrade()[q], str(cl.getNumerator()[q]), str(cl.getDenominator()[q]))))
                    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = MainWindow()
    form.resize(960,540)
    form.show()
    sys.exit(app.exec_())
