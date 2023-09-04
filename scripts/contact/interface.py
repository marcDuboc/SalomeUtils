# -*- coding: utf-8 -*-
# GUI module for contact
# License: LGPL v 3.0
# Autor: Marc DUBOC
# Version: 28/08/2023

import os
import time
import inspect
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QWidget, QGridLayout, QComboBox, QItemDelegate, QLabel, QLineEdit,QTableView,QStyle 
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal, pyqtSlot, QEvent


root_path= os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
img_path = os.path.join(root_path, 'img')


DEBUG_FILE = 'E:\GitRepo\SalomeUtils\debug\d.txt'

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
    swap = pyqtSignal(int)  # Signal avec l'ID de la ligne en argument

    def __init__(self, *args, **kwargs):
        super(SwapDelegate, self).__init__(*args, **kwargs)

    def paint(self, painter, option, index):
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor.fromRgb(200, 200, 200))
    
        if index.isValid():
            icon = QIcon(os.path.join(img_path,'swap.png'))
            icon.paint(painter, option.rect, Qt.AlignCenter)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease:
            # get the id from the data model
            row= index.row()
            value= model.data(model.index(row,0), Qt.DisplayRole)
            self.swap.emit(value)
            return True
        
        return super(SwapDelegate, self).editorEvent(event, model, option, index)

class HideShowDelegate(QItemDelegate):
    hideShow = pyqtSignal(int,bool)

    def __init__(self, *args, **kwargs):
        super(HideShowDelegate, self).__init__(*args, **kwargs)

    def paint(self, painter, option, index):
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor.fromRgb(200, 200, 200, 255))
    
        if index.isValid():
            if index.model().data(index, Qt.DisplayRole) == False:
                icon = QIcon(os.path.join(img_path,'hide.png'))
            else:
                icon = QIcon(os.path.join(img_path,'display.png'))
            icon.paint(painter, option.rect, Qt.AlignCenter)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease:
            # Émettez le signal avec l'ID de la ligne comme argument
            id = index.model().data(index.siblingAtColumn(0), Qt.DisplayRole)
            value = model.data(index, Qt.DisplayRole)

            if value == True:
                self.hideShow.emit(id,False)
                # set data to table model
                model.setData(index, False, Qt.EditRole)

            else:
                self.hideShow.emit(id,True)
                # set data to table model.
                model.setData(index, True, Qt.EditRole)

            return True
        return super(HideShowDelegate, self).editorEvent(event, model, option, index)

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
            try:
                return self._data[index.row()][index.column()]
            except IndexError:
                return ''

        # background color
        if role == Qt.BackgroundRole:
            if index.column() == 5:
                return QColor(Qt.gray)
            
        if role == Qt.DecorationRole:
            if index.column() == 5:
                return QIcon(os.path.join(img_path,'delete.png'))

    def setData(self, index, value, role=Qt.EditRole):		
        if role in (Qt.DisplayRole, Qt.EditRole):
            with open(DEBUG_FILE, 'a') as f:
                f.write(time.ctime())
                f.write('\t')
                f.write('setData'+'\t')
                f.write(str(index.row())+'\t')
                f.write(str(index.column())+'\t')
                f.write(str(value))
                f.write('\n')

            # if value is blank
            if value in ('',' '):
                return False

            self._data[index.row()][index.column()] = value
            with open(DEBUG_FILE, 'a') as f:
                f.write(time.ctime())
                f.write('\t')
                f.write(str(self._data)+'\t')
                f.write('\n')

            #self.dataChanged.emit(index, index)



        return True
        
    def flags(self, index):
        default_flags = super(TableModel, self).flags(index)
        if index.column() in (0,1,3,4):  
            return default_flags & ~Qt.ItemIsEditable
        return default_flags | Qt.ItemIsEditable
    
    def update_database(self, index):
        print('update database', index.row(), index.column())
        # update database
        #self._data[row][0] = 'updated'
        #self.dataChanged.emit(index, index)

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
    closing = pyqtSignal()

    def __init__(self):
        super(ContactGUI, self).__init__()
        self._data = []
        self.init_UI()       

    def closeEvent(self, event):
        print("Fermeture de la fenêtre, suppression des instances...")
        self.closing.emit()
        event.accept()  # Ferme la fenêtre """

    def init_UI(self):
        # Table model
        self.model = TableModel(self._data)
        self.typeItem = TypeDelegate()
        self.deleteItem = DeleteDelegate()
        self.swapItem = SwapDelegate()
        self.hideShowItem = HideShowDelegate()

        self.table_view = QTableView(self)
        self.table_view.setItemDelegateForColumn(2, self.typeItem)
        self.table_view.setItemDelegateForColumn(5, self.deleteItem)
        self.table_view.setItemDelegateForColumn(4, self.swapItem)
        self.table_view.setItemDelegateForColumn(3, self.hideShowItem)

        # select root component
        self.l_root = QLabel("Root compound: ", self)
        self.lb_root = QLineEdit()
        self.lb_root.setReadOnly(True)
        self.lb_root.setText("Please select a compound")
        self.bt_root = QPushButton()
        self.bt_root.setText("Load")
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
        print('set data \t',data)
        # add 2 extra columns for the button (delete)
        for d in range(len(data)):
            data[d].append('')
            data[d].append('')
        if len(data) > 0:
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
        # 
          
    
