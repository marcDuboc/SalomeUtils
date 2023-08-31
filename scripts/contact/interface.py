# -*- coding: utf-8 -*-
# GUI module for contact
# License: LGPL v 3.0
# Autor: Marc DUBOC
# Version: 28/08/2023

import os
import inspect
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QWidget, QGridLayout, QComboBox, QItemDelegate, QLabel, QLineEdit,QTableView
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal, pyqtSlot


root_path= os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
img_path = os.path.join(root_path, 'img')


class Controler():
    def __init__(self):
        self.data=None

    def updateData(self):
        pass

    def setData(self,data):
        self.data=data

class TypeDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(['BONDED', 'SLIDING', 'FRICTION','FRICTIONLESS'])
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        editor.setCurrentText(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)

class DeleteDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QPushButton("Delete",parent)
        editor.clicked.connect(lambda: self.deleteRow(index))
        return editor

    def deleteRow(self, index):
        # You can add logic here to call your external function, like:
        # your_function(index.model().data(index.siblingAtColumn(0), Qt.EditRole))
        index.model().removeRow(index.row())

class SwapDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QPushButton("Swap",parent)
        editor.clicked.connect(lambda: self.setModelData(index))
        return editor

    def setModelData(self,editor, model,index):
        # swap value 0 <-> 1 in the model data
        if index.model().data(index, Qt.EditRole) == 0:
            model.setData(index, 1, Qt.EditRole)
        else:
            model.setData(index, 0, Qt.EditRole) 

class HideShowDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QPushButton("Hide/Show",parent)
        editor.clicked.connect(lambda: self.setModelData(index))
        return editor

    def setModelData(self, editor, model,index):
        # swap value 0 <-> 1 in the model data
        if index.model().data(index, Qt.EditRole) == 0:
            model.setData(index, 1, Qt.EditRole)
            print('set to 1')

        else:
            model.setData(index, 0, Qt.EditRole)
            print('set to 0')

class TableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(max(self._data, key=len))

    def data(self, index, role=Qt.DisplayRole):
        # display data
        if role == Qt.DisplayRole:
            print('Display role:', index.row(), index.column())
            try:
                return self._data[index.row()][index.column()]
            except IndexError:
                return ''
            
        # background color
        if role == Qt.BackgroundRole:
            if index.column() == 4:
                return QtGui.QColor(Qt.gray)
            
        if role == Qt.DecorationRole:
            if index.column() == 4:
                return QtGui.QIcon(os.path.join(img_path,'delete.png'))
            elif index.column() == 3:
                return QtGui.QIcon(os.path.join(img_path,'swap.png'))
            elif index.column() == 2:
                # if value is 0
                if self._data[index.row()][index.column()] == 0:
                    return QtGui.QIcon(os.path.join(img_path,'hide.png'))
                else:
                    return QtGui.QIcon(os.path.join(img_path,'display.png'))
            

    def setData(self, index, value, role=Qt.EditRole):
        print(self._data)		
        if role in (Qt.DisplayRole, Qt.EditRole):
            print('Edit role:', index.row(), index.column())
            # if value is blank
            if not value:
                return False	
            self._data[index.row()][index.column()] = value
            self.dataChanged.emit(index, index)
        return True
        
    def flags(self, index):
        return super().flags(index) | Qt.ItemIsEditable
    

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        # header data
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return 'Column {}'.format(section)
            else:
                return 'Row {}'.format(section)
    
    def insertRows(self, position, rows, parent=QModelIndex()):
        self.beginInsertRows(parent, position, position + rows - 1)
        for i in range(rows):
            self._data.insert(position, [''] * self.columnCount())
        self.endInsertRows()
        return True
    
    def removeRows(self, position, rows, parent=QModelIndex()):
        self.beginRemoveRows(parent, position, position + rows - 1)
        for i in range(rows):
            del self._data[position]
        self.endRemoveRows()
        return True
    
class SecondaryWindow(QWidget):
    dataReady = pyqtSignal(object)  # Define the custom signal

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Secondary Window')
        label = QLabel('This is a secondary window.')
        layout = QVBoxLayout()
        layout.addWidget(label)
        bt = QPushButton('Ok')
        layout.addWidget(bt)
        self.setLayout(layout)
        bt.clicked.connect(self.sendData)

    def sendData(self):
        # Emit the custom signal with the data you want to send
        # (replace "your_data_here" with the actual data)
        self.dataReady.emit("your_data_here")

class ContactGUI(QWidget):

    # define custom signals
    load_compound = pyqtSignal()

    def __init__(self):
        super(ContactGUI, self).__init__()
        self._data = [['id1', 'BONDED', 1, 1,''],['id2', 'BONDED', 0, 1,''],['id3', 'BONDED', 1, 0,''],]
        self.init_UI()        

    def init_UI(self):
        # Table model
        self.model = TableModel(self._data)
        self.typeItem = TypeDelegate()
        self.deleteItem = DeleteDelegate()
        self.swapItem = SwapDelegate()
        self.hideShowItem = HideShowDelegate()

        self.table_view = QTableView(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegateForColumn(1, self.typeItem)
        self.table_view.setItemDelegateForColumn(5, self.deleteItem)
        self.table_view.setItemDelegateForColumn(3, self.swapItem)
        self.table_view.setItemDelegateForColumn(2, self.hideShowItem)

        # select root component
        self.l_root = QLabel("Root component: ", self)
        self.lb_root = QLineEdit()
        self.bt_root = QPushButton()
        self.bt_root.setText("Load compound")
        self.bt_root.clicked.connect(self.emit_load_compound)

        btnOK = QPushButton('OK')

        btnSecondary = QPushButton('Open Secondary Window')
        btnSecondary.clicked.connect(self.openSecondaryWindow)

        # layout
        layout = QGridLayout()
        layout.addWidget(self.l_root, 1, 0)
        layout.addWidget(self.lb_root, 2, 0)
        layout.addWidget(self.bt_root, 2, 1)
        layout.addWidget(self.table_view, 3, 0, 1, 2)
        layout.addWidget(btnOK, 4, 0)
        layout.addWidget(btnSecondary, 4, 1)
        self.setLayout(layout)
        
    # slots
    @pyqtSlot(str)
    def on_compound_selected(self, master_compound_name):
        self.lb_root.setText(master_compound_name)

    # signals emitters
    def emit_load_compound(self):
        self.load_compound.emit()

    def set_data(self, data):
        self.model = TableModel(data)
        self.table_view.setModel(self.model)    

    # This method will be called when the button is clicked
    def openSecondaryWindow(self):
        self.secondaryWindow = SecondaryWindow()
        self.secondaryWindow.dataReady.connect(self.receiveData)
        self.secondaryWindow.show()


    def receiveData(self, data):
        # This method will be called when the dataReady signal is emitted
        print(f"Received data: {data}")
        # Update your model or GUI here        
    
