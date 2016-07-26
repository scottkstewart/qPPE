#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import (QMainWindow, QApplication, QListWidget, QDockWidget, QVBoxLayout, QWidget, QAction, QStyle, QFrame, QLabel)
from PyQt5.QtCore import Qt

__version__ = "1.0.0"

class MainWindow(QMainWindow):
    """Class to display current status of LCPS' StudentVue"""
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("StudentVue")

        self.listview = QListWidget()
        self.listview.addItems([chr(i)*20 for i in range(ord('A'), ord('Z')+1)]*5)
        self.setCentralWidget(self.listview)
        
        accountDoc = QDockWidget("Accounts", self)
        accountDoc.setObjectName("Accounts")
        accountDoc.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.accountlist = QListWidget()
        self.accountlist.addItems([str(i) for i in range(50)])
        self.classlist = QListWidget()
        self.classlist.addItems(["AP {} {}".format(chr(i)*5, "Theory" if i%2 else "Science") for i in range(ord('A'), ord('H'))])
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = MainWindow()
    form.show()
    sys.exit(app.exec_())
