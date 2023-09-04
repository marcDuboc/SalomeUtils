# -*- coding: utf-8 -*-
# GUI module for contact
# License: LGPL v 3.0
# Autor: Marc DUBOC
# Version: 28/08/2023

import os
import time
import inspect
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QWidget, QGridLayout, QComboBox, QItemDelegate, QLabel, QLineEdit,QTableView,QStyle, QGroupBox, QHBoxLayout,QDoubleSpinBox, QCheckBox
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal, pyqtSlot, QEvent


root_path= os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
img_path = os.path.join(root_path, 'img')


DEBUG_FILE = 'E:\GitRepo\SalomeUtils\debug\d.txt'


class TypeDelegate(QItemDelegate):
    changeType = pyqtSignal(int,str) 
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(['BONDED', 'SLIDING', 'FRICTION','FRICTIONLESS'])
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        editor.setCurrentText(value)

    def setModelData(self, editor, model, index):
        # send signal to update contact type
        id = index.model().data(index.siblingAtColumn(0), Qt.DisplayRole)
        self.changeType.emit(id,editor.currentText())
        # update view
        model.setData(index, editor.currentText(), Qt.EditRole)

class DeleteDelegate(QItemDelegate):
    delContact = pyqtSignal(int) 

    def __init__(self, *args, **kwargs):
        super(DeleteDelegate, self).__init__(*args, **kwargs)

    def paint(self, painter, option, index):
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor.fromRgb(200, 200, 200))
    
        if index.isValid():
            icon = QIcon(os.path.join(img_path,'delete.png'))
            icon.paint(painter, option.rect, Qt.AlignCenter)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease:
            # get the id from the data model
            id = index.model().data(index.siblingAtColumn(0), Qt.DisplayRole)
            model.removeRows(index.row(),1)
            self.delContact.emit(id)
            return True
        
        return super(DeleteDelegate, self).editorEvent(event, model, option, index)

class SwapDelegate(QItemDelegate):
    swap = pyqtSignal(int)  # Signal avec l'ID de la ligne en argument

    def __init__(self, *args, **kwargs):
        super(SwapDelegate, self).__init__(*args, **kwargs)

    """def event(self, event):
        if event.type() == QEvent.HoverEnter:
            print("enter")
        elif event.type() == QEvent.HoverLeave:
            print("leave")
        return super().event(event)"""

    def paint(self, painter, option, index):

        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor.fromRgb(200, 200, 200))
    
        if index.isValid():
            icon = QIcon(os.path.join(img_path,'swap.png'))
            icon.paint(painter, option.rect, Qt.AlignCenter)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease:
            # get the id from the data model
            id = index.model().data(index.siblingAtColumn(0), Qt.DisplayRole)
            self.swap.emit(id)
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

        return True
        
    def flags(self, index):
        default_flags = super(TableModel, self).flags(index)
        if index.column() in (0,1,3,4):  
            return default_flags & ~Qt.ItemIsEditable
        return default_flags | Qt.ItemIsEditable

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

class AutoWindows(QWidget):
    partSelection = pyqtSignal()
    contactRun = pyqtSignal(float,float,bool)

    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Auto contact creation')

        layout = QGridLayout()

        #parts selection
        self.l_p = QLabel("Parts selection: ", self)
        self.le_p = QLineEdit()
        self.le_p.setReadOnly(True)
        self.le_p.setText("Please select at least 2 parts")
        self.bt_p = QPushButton()
        self.bt_p.setText("Load")

        # Adjust Gap
        self.l_gap = QLabel("Max gap between (model unit): ")
        self.sb_gap = QDoubleSpinBox()
        self.sb_gap.setDecimals(3)
        self.sb_gap.setValue(0.000)
        self.sb_gap.setSingleStep(0.001)

        # Adjust coincidcence tolerance
        self.l_ctol = QLabel("Cylinder coincidence tolerance (radian): ")
        self.sb_ctol = QDoubleSpinBox()
        self.sb_ctol.setDecimals(3)
        self.sb_ctol.setValue(0.01)
        self.sb_ctol.setSingleStep(0.001)

        # create groupbox options
        self.gp_options = QGroupBox("Options", self)

        # create checkbox avoid slave neighborhood
        self.cb_avoid = QCheckBox("Avoid self slave neighborhood", self)
        self.cb_avoid.setChecked(True)

        # put the checkbox in a horizontal layout
        self.hbox_options = QHBoxLayout()
        self.hbox_options.addWidget(self.cb_avoid)
        self.gp_options.setLayout(self.hbox_options)

        # add run button
        self.bt_run = QPushButton("Run", self)

        # add cancel button
        self.bt_cancel = QPushButton("Cancel", self)

        # put the buttons in a horizontal layout
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.bt_run)
        self.hbox.addWidget(self.bt_cancel)

        layout.addWidget(self.l_p, 1, 0)
        layout.addWidget(self.le_p, 2, 0)
        layout.addWidget(self.bt_p, 2, 1)
        layout.addWidget(self.l_gap, 3, 0)
        layout.addWidget(self.sb_gap, 3, 1)
        layout.addWidget(self.l_ctol, 4, 0)
        layout.addWidget(self.sb_ctol, 4, 1)
        layout.addWidget(self.gp_options, 5, 0, 1, 2)
        layout.addWidget(self.bt_run, 6, 0)
        layout.addWidget(self.bt_cancel, 6, 1)
        self.setLayout(layout)

        # connect signals
        self.bt_p.clicked.connect(self.emit_part_selection)
        self.bt_run.clicked.connect(self.emit_run)
        self.bt_cancel.clicked.connect(self.hide)
    
    def emit_part_selection(self):
        self.partSelection.emit()

    def emit_run(self):
        # get the values
        gap = self.sb_gap.value()
        ctol = self.sb_ctol.value()
        avoid = self.cb_avoid.isChecked()
        with open(DEBUG_FILE, 'a') as f:
            f.write(time.ctime())
            f.write('\t')
            f.write('emit_run'+'\t')
            f.write(str(gap)+'\t')
            f.write(str(ctol)+'\t')
            f.write(str(avoid)+'\t')
            f.write('\n')
        self.contactRun.emit(gap,ctol,avoid)

    @pyqtSlot(list)
    def set_parts(self, parts):
        self.partSelected = parts
        nb_parts = len(parts)
        if nb_parts ==0 :
            msg = 'Please select at least 2 parts !'
        else:
            msg = f'{nb_parts} parts selected'
        self.le_p.setText(msg)


class ManualWindows(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUi(self):
        self.setWindowTitle('Manual Contact creation')

class ContactGUI(QWidget):

    # define custom signals
    load_compound = pyqtSignal()
    closing = pyqtSignal()

    def __init__(self):
        super(ContactGUI, self).__init__()
        self._data = []
        self.init_UI()
        self.autoWindow = AutoWindows()
        self.autoWindow.setWindowFlags(self.autoWindow.windowFlags() | Qt.WindowStaysOnTopHint)
        self.autoWindow.hide()

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

        # group for contact creation
        self.gp_contact = QGroupBox("Create contact", self)

        # create buttons for contact creation
        self.bt_contact_auto = QPushButton("Auto", self)
        self.bt_contact_manual = QPushButton("Manual", self)

        # put the bouton in a horizontal layout
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.bt_contact_auto)
        self.hbox.addWidget(self.bt_contact_manual)
        self.gp_contact.setLayout(self.hbox)

        # create button OK	
        btnOK = QPushButton('Ok')

        # layout
        layout = QGridLayout()
        layout.addWidget(self.l_root, 1, 0)
        layout.addWidget(self.lb_root, 2, 0)
        layout.addWidget(self.bt_root, 2, 1)
        layout.addWidget(self.table_view, 3, 0, 1, 2)
        layout.addWidget(self.gp_contact, 4, 0, 1, 2)
        layout.addWidget(btnOK, 5, 1)
        self.setLayout(layout)

        # connect signals
        self.bt_contact_auto.clicked.connect(self.openAutoWindow)
        btnOK.clicked.connect(self.close)
        
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

    def openAutoWindow(self):
        self.autoWindow.show()  

    def receiveData(self, data):
        # This method will be called when the dataReady signal is emitted
        print(f"Received data: {data}")
        # Update your model or GUI here  
        # 
          
    
