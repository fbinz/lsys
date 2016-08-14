from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import vispy
import vispy.scene
import vispy.visuals
import numpy as np
import math

class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        splitter = QSplitter()
        self.setCentralWidget(splitter)

        sub_layout = QFormLayout()
        sub_layout.setWidget(0, QFormLayout.SpanningRole, QLabel('DOL System Demo'))
        sub_layout.setLabelAlignment(Qt.AlignRight)
        self.iteration_input = QSpinBox()
        self.iteration_input.setMaximum(20)
        sub_layout.addWidget(self.iteration_input)
        sub_layout.addRow('N:', self.iteration_input)
        self.axiom_input = QLineEdit('F-F-F-F')
        sub_layout.addRow('Axiom:', self.axiom_input)
        self.angle_increment = QSpinBox()
        self.angle_increment.setMaximum(180)
        self.angle_increment.setMinimum(-180)
        sub_layout.addRow('Angle Increment [°]:', self.angle_increment)
        group = QGroupBox('Rules')
        group_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        self.add_button = QPushButton('+')
        self.add_button.clicked.connect(self.add_rule)
        self.remove_button = QPushButton('-')
        self.remove_button.clicked.connect(self.remove_rule)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        group_layout.addLayout(button_layout)
        self.rule_list = QListWidget()
        self.rule_list.itemDoubleClicked.connect(self.edit_rule)
        self.rule_list.setSelectionMode(QListWidget.SingleSelection)
        group_layout.addWidget(self.rule_list)
        group.setLayout(group_layout)
        sub_layout.setWidget(5, QFormLayout.SpanningRole, group)
        refresh_button = QPushButton('Refresh')
        refresh_button.clicked.connect(self.refresh_display)
        sub_layout.setWidget(6, QFormLayout.SpanningRole, refresh_button)

        dummy = QWidget()
        dummy.setLayout(sub_layout)
        splitter.addWidget(dummy)

        self.canvas = vispy.scene.SceneCanvas(keys='interactive')
        self.canvas.bgcolor = (1, 1, 1)
        self.canvas.create_native()
        splitter.addWidget(self.canvas.native)

        self.view = self.canvas.central_widget.add_view()
        self.view.camera = vispy.scene.PanZoomCamera(aspect=1)
        self.view.camera.center = (0, 0)
        self.view.border_color = 'black'
        self.line = vispy.scene.visuals.Line(pos=np.array([(0, 0), (0, 0)]), color='black', width=1,
                                             connect='segments', parent=self.view.scene)

        # add default rule for quadratic Koch island
        self.rule_list.addItem(QListWidgetItem('F -> F - F + F + F F - F - F + F'))
        self.angle_increment.setValue(90)

    def add_rule(self):
        item = QListWidgetItem()
        self.rule_list.addItem(item)
        self.edit_rule(item)

    def remove_rule(self):
        row = self.rule_list.currentRow()
        if row is -1:
            n = self.rule_list.count()
            if n > 0:
                self.rule_list.takeItem(n - 1)
        else:
            self.rule_list.takeItem(row)

    def edit_rule(self, item):
        dialog = QInputDialog(self)
        dialog.setLabelText('Enter Rule (Alphabet: F, Fl, Fr, f)')
        dialog.setTextValue(item.text())
        if dialog.exec_():
            rule = dialog.textValue()
            item.setText(rule)

    def refresh_display(self):
        # parse rules and validate input
        rules = []
        error = False
        for row in range(self.rule_list.count()):
            item = self.rule_list.item(row)
            try:
                [predecessor, successor] = item.text().split('->')
                predecessor = predecessor.strip()
                assert predecessor in ['F', 'Fl', 'Fr', 'f']
                for s in successor:
                    s = s.strip()
                    if not s:  # s was whitespace
                        continue
                    assert s in ['F', 'Fl', 'Fr', 'f', '+', '-']
                rules.append((predecessor, successor))
            except:
                item.setBackground(QBrush(QColor(255, 0, 0, 122)))
        if error:
            return

        rules = dict(rules)

        # apply rules to axiom
        drawing = self.axiom_input.text()
        for _ in range(int(self.iteration_input.text())):
            result = []
            for c in drawing:
                if c in rules:
                    result.append(rules[c])
                else:
                    result.append(c)
            drawing = ''.join(result)

        # draw turtle graphics
        angle_increment = math.radians(int(self.angle_increment.text()))
        angle = 0
        p0 = np.array((0, 0))
        pos = []
        for c in drawing:
            if c == 'F':
                p1 = p0 + np.array((math.sin(angle), math.cos(angle)))
                pos.append(p0)
                pos.append(p1)
                p0 = p1
            if c == 'f':
                # note: += would modify p0, so the object appended in pos.append(p0) above is modified aswell, which
                # is not intended!
                p0 = p0 + np.array((math.sin(angle), math.cos(angle)))
            elif c == '+':
                angle += angle_increment
            elif c == '-':
                angle -= angle_increment
        if not pos:
            pos = np.array([(0, 0), (0, 0)])
        pos = np.array(pos)
        self.line.set_data(pos=pos)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
