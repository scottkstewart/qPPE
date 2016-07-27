#!/usr/bin/env python3
import sys
import re
import shelve
from PyQt5.QtWidgets import (QMainWindow, QApplication, QListWidget, QDockWidget, QVBoxLayout, QWidget, QAction, QStyle, QFrame, QLabel, QTableWidget, QHeaderView, QTableWidgetItem)
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

        self.gradetable = QTableWidget(self)
        self.gradetable.setColumnCount(5)
        self.gradetable.setHorizontalHeaderLabels(('Assignment', 'Numerator', 'Denominator', 'Percentage', 'Grade'))
        self.gradetable.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch)
        self.setCentralWidget(self.gradetable)
        self.gradetable.setAlternatingRowColors(True)
        
        accountDoc = QDockWidget("Class Picker", self)
        accountDoc.setObjectName("Class Picker")
        accountDoc.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.accountlist = QListWidget()
        self.accountlist.setAlternatingRowColors(True)
        self.accountlist.itemPressed.connect(self.updateui)
        self.classlist = QListWidget()
        self.classlist.setAlternatingRowColors(True)
        self.classlist.itemPressed.connect(self.updateui)
        dockLayout = QVBoxLayout()
        dockLayout.addWidget(self.accountlist)
        dockLayout.addWidget(self.classlist)
        dockWidget = QWidget()
        dockWidget.setLayout(dockLayout)
        accountDoc.setWidget(dockWidget)
        self.addDockWidget(Qt.LeftDockWidgetArea, accountDoc)

        aboutAction = QAction("&About", self)
        aboutAction.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
        settingsAction = QAction("&Settings", self)
        settingsAction.setIcon(self.style().standardIcon(QStyle.SP_TitleBarContextHelpButton))
        quitAction = QAction("&Quit", self)
        quitAction.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))

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
                cl.setAssignments([('({}) Assignment number {}.'.format(key, i+1), 'G ({}/100)'.format(100-i)) for i in range(15)])

        self.updateui()

    def updateui(self):
        ind = self.accountlist.currentRow()
        self.accountlist.clear()
        self.accountlist.addItems(sorted(self.accounts.keys()))
        self.accountlist.setCurrentRow(ind)
      
        ind = self.classlist.currentRow()
        self.classlist.clear()
        if self.accountlist.currentItem() is not None:
            self.classlist.addItems((cl.getName() for cl in self.accounts[self.accountlist.currentItem().text()].classes))
            self.classlist.setCurrentRow(ind)
        
        if self.classlist.currentItem() is not None:
            assignmentList = self.accounts[self.accountlist.currentItem().text()].classes[ind].getAssignments()
            self.gradetable.setRowCount(len(assignmentList))
            for row, assignment in enumerate(assignmentList):
                grade, num, denom = re.split("[/()]",assignment[1])[:3]
                self.gradetable.setItem(row, 0, QTableWidgetItem(assignment[0]))
                self.gradetable.setItem(row, 1, QTableWidgetItem(num))
                self.gradetable.setItem(row, 2, QTableWidgetItem(denom))
                self.gradetable.setItem(row, 3, QTableWidgetItem('{:0.1f}%'.format(int(num)/int(denom)*100)))
                self.gradetable.setItem(row, 4, QTableWidgetItem(grade[:-1]))
                for i in range(0, 5): self.gradetable.item(row, i).setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable) 

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = MainWindow()
    form.resize(960,540)
    form.show()
    sys.exit(app.exec_())
