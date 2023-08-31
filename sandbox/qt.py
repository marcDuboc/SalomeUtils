from PyQt5.QtWidgets import QWidget, QLineEdit, QDockWidget
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, Qt
import sys

class ContactGUI(QWidget):
    def __init__(self):
        super(ContactGUI, self).__init__()
        self.initUI()

    def initUI(self):
        self.lb_root = QLineEdit(self)

    @pyqtSlot(str)
    def on_compound_selected(self, master_compound_name):
        self.lb_root.setText(master_compound_name)

class ContactAuto(QObject):
    compound_selected = pyqtSignal(str)

    def __init__(self):
        super(ContactAuto, self).__init__()
        self.Gui = ContactGUI()
        self.compound_selected.connect(self.Gui.on_compound_selected)

    @pyqtSlot()
    def select_compound(self):
        self.compound_selected.emit("Example")

#app = QApplication(sys.argv)

contact_auto_instance = ContactAuto()

d = QDockWidget()
d.setWidget(contact_auto_instance.Gui)
d.setAttribute(Qt.WA_DeleteOnClose)
d.setWindowTitle("3D Contacts")
d.setGeometry(600, 300, 400, 400)
d.show()

# Simulating compound selection
contact_auto_instance.select_compound()

#sys.exit(app.exec_())