# -*- coding: utf-8 -*-
# abstract item for gui module
# License: LGPL v 3.0
# Autor: Marc DUBOC
# Version: 28/08/2023

import os
from PyQt5.QtWidgets import QComboBox, QItemDelegate,QStyle
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal, QEvent
from contact.cgui import IMG_PATH
from contact import logging

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
            icon = QIcon(os.path.join(IMG_PATH,'delete.png'))
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

    def paint(self, painter, option, index):

        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor.fromRgb(200, 200, 200))
    
        if index.isValid():
            icon = QIcon(os.path.join(IMG_PATH,'swap.png'))
            icon.paint(painter, option.rect, Qt.AlignCenter)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease:
            # get the id from the data model
            id = index.model().data(index.siblingAtColumn(0), Qt.DisplayRole)

            # swap value between column 3 and 4
            value_3 = index.model().data(index.siblingAtColumn(3), Qt.DisplayRole)
            value_4 = index.model().data(index.siblingAtColumn(4), Qt.DisplayRole)
            model.setData(index.siblingAtColumn(3), value_4, Qt.EditRole)
            model.setData(index.siblingAtColumn(4), value_3, Qt.EditRole)
            
            # update view
            
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
                icon = QIcon(os.path.join(IMG_PATH,'hide.png'))
            else:
                icon = QIcon(os.path.join(IMG_PATH,'display.png'))
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
    def __init__(self, data, header=None):
        super().__init__()
        self._data = data
        self.header=['ID','Name','Type','Master','Slave','Display','Swap','Delete']

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        try:
            nbcol= len(max(self._data, key=len))
            return nbcol
        except ValueError:
            return len(self.header)

    def data(self, index, role=Qt.DisplayRole):
        # display data
        if role == Qt.DisplayRole:
            try:
                return self._data[index.row()][index.column()]
            except IndexError:
                return ''

    def setData(self, index, value, role=Qt.EditRole):		
        if role in (Qt.DisplayRole, Qt.EditRole):
            # if value is blank
            if value in ('',' '):
                return False
            self._data[index.row()][index.column()] = value
            self.dataChanged.emit(index, index)
        return True
        
    def flags(self, index):
        default_flags = super(TableModel, self).flags(index)
        if index.column() in (0,1,3,4,5,6,7):  
            return default_flags & ~Qt.ItemIsEditable
        return default_flags | Qt.ItemIsEditable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        # header data
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return '{}'.format(self.header[section])

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