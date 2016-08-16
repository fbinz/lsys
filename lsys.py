# -*- coding: utf-8
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
        sub_layout.setLabelAlignment(Qt.AlignRight)
        sub_layout.setWidget(0, QFormLayout.SpanningRole, QLabel('L-System Demo'))
        self.load_examples_box = QComboBox()
        for s in MainWindow.EXAMPLES.keys():
            self.load_examples_box.addItem(s)
        self.load_examples_box.currentTextChanged.connect(self.load_example)
        sub_layout.addRow('Load Example:', self.load_examples_box)
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
        sub_layout.setWidget(6, QFormLayout.SpanningRole, group)
        refresh_button = QPushButton('Refresh')
        refresh_button.clicked.connect(self.refresh_display)
        group = QGroupBox('Drawing')
        group_layout = QFormLayout()
        group_layout.setLabelAlignment(Qt.AlignRight)
        self.starting_angle_input = QSpinBox()
        self.starting_angle_input.setMaximum(180)
        self.starting_angle_input.setMinimum(-180)
        group_layout.addRow('Starting Angle [°]', self.starting_angle_input)
        self.draw_characters_input = QLineEdit('FG')
        group_layout.addRow('Draw', self.draw_characters_input)
        self.skip_characters_input = QLineEdit('fg')
        group_layout.addRow('Skip', self.skip_characters_input)
        self.turn_left_characters_input = QLineEdit('+')
        group_layout.addRow('Turn Left', self.turn_left_characters_input)
        self.turn_right_characters_input = QLineEdit('-')
        group_layout.addRow('Turn Right', self.turn_right_characters_input)
        group.setLayout(group_layout)
        sub_layout.setWidget(7, QFormLayout.SpanningRole, group)
        sub_layout.setWidget(8, QFormLayout.SpanningRole, refresh_button)

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

        # create status bar
        self.statusBar()

        self.load_examples_box.setCurrentText('Fractal plant')

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
                assert len(predecessor) == 1, 'For now, only single character predecessor strings are allowed'
                rules.append((predecessor, successor))
            except Exception as e:
                item.setBackground(QBrush(QColor(255, 0, 0, 122)))
                self.statusBar().showMessage(e.args[0], 5000)
                error = True
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
        stack = []
        angle_increment = math.radians(int(self.angle_increment.text()))
        angle = self.starting_angle_input.value()
        p0 = np.array((0, 0))
        pos = []
        draw_chars = self.draw_characters_input.text()
        skip_chars = self.skip_characters_input.text()
        left_chars = self.turn_left_characters_input.text()
        right_chars = self.turn_right_characters_input.text()
        for c in drawing:
            if c in draw_chars:
                p1 = p0 + np.array((math.sin(angle), math.cos(angle)))
                pos.append(p0)
                pos.append(p1)
                p0 = p1
            if c in skip_chars:
                # note: += would modify p0, so the object appended in pos.append(p0) above is modified aswell, which
                # is not intended!
                p0 = p0 + np.array((math.sin(angle), math.cos(angle)))
            elif c == left_chars:
                angle += angle_increment
            elif c == right_chars:
                angle -= angle_increment
            elif c == '[':
                stack.append((angle, p0))
            elif c == ']':
                angle, p0 = stack.pop()
        if not pos:
            pos = np.array([(0, 0), (0, 0)])
        pos = np.array(pos)

        self.statusBar().showMessage('Finished drawing {} vertices.'.format(len(pos)), 5000)
        self.line.set_data(pos=pos)

    def clear_all(self):
        self.rule_list.clear()
        self.angle_increment.setValue(0)
        self.draw_characters_input.clear()
        self.axiom_input.clear()
        self.skip_characters_input.clear()
        self.turn_left_characters_input.clear()
        self.turn_right_characters_input.clear()

    def load_example(self, name):
        example = MainWindow.EXAMPLES.get(name)
        if not example:
            return

        self.clear_all()
        for rule in example['rules']:
            self.rule_list.addItem(QListWidgetItem(rule))
        self.axiom_input.setText(example.get('axiom'))
        self.draw_characters_input.setText(example.get('draw'))
        self.skip_characters_input.setText(example.get('skip'))
        self.turn_right_characters_input.setText(example.get('turn_right'))
        self.turn_left_characters_input.setText(example.get('turn_left'))
        self.angle_increment.setValue(example.get('angle_increment') or 0)
        self.starting_angle_input.setValue(example.get('starting_angle') or 0)
        self.iteration_input.setValue(example.get('N') or 0)

    EXAMPLES = {
        'Pytagoras Tree': {
            'rules': [
                '1 -> 11',
                '0 -> 1[+0]-0'
            ],
            'axiom': '0',
            'draw': '01',
            'angle_increment': 45,
            'turn_left': '+',
            'turn_right': '-',
            'starting_angle': 0,
            'N': 5,
        },
        'Koch curve': {
            'rules': [
                'F -> F+F-F-F+F'
            ],
            'axiom': 'F',
            'draw': 'F',
            'angle_increment': 90,
            'turn_left': '+',
            'turn_right': '-',
            'starting_angle': 0,
            'N': 5,
        },
        'Sierpinski triangle': {
            'rules': [
                'A -> +B-A-B+',
                'B -> -A+B+A-'
            ],
            'axiom': 'A',
            'draw': 'AB',
            'angle_increment': 60,
            'turn_left': '+',
            'turn_right': '-',
            'starting_angle': 0,
            'N': 5,
        },
        'Dragon curve': {
            'rules': [
                'X -> X+YF+',
                'Y -> -FX-Y'
            ],
            'axiom': 'FX',
            'draw': 'F',
            'angle_increment': 90,
            'turn_left': '+',
            'turn_right': '-',
            'starting_angle': 0,
            'N': 5,
        },
        'Fractal plant': {
            'rules': [
                'X -> F-[[X]+X]+F[+FX]-X',
                'F -> FF'
            ],
            'axiom': 'X',
            'draw': 'F',
            'angle_increment': 25,
            'turn_left': '+',
            'turn_right': '-',
            'starting_angle': -25,
            'N': 6,
        },
        'Fractal bushy thing': {
            'rules': [
                'F -> FF-[-F+F+F]+[+F-F-F]',
            ],
            'axiom': 'F',
            'draw': 'F',
            'angle_increment': 22.5,
            'turn_left': '+',
            'turn_right': '-',
            'starting_angle': 0,
            'N': 4,
        },
        'Another plant...': {
            'rules': [
                'F -> F[+F]F[-F][F]',
            ],
            'axiom': 'F',
            'draw': 'F',
            'angle_increment': 20,
            'turn_left': '+',
            'turn_right': '-',
            'starting_angle': 0,
            'N': 5,
        },
        'FASS example': {
            'rules': [
                'L->LF+RFR+FL-F-LFLFL-FRFR+',
                'R->-LFLF+RFRFR+F+RF-LFL-FR',
            ],
            'axiom': '-L',
            'draw': 'F',
            'angle_increment': 90,
            'turn_left': '+',
            'turn_right': '-',
            'starting_angle': 0,
            'N': 3,
        },
        'Island and lakes': {
            'rules': [
                'F -> F+f-FF+F+FF+Ff+FF-f+FF-F-FF-Ff-FFF',
                'f -> fffffff'
            ],
            'axiom': 'F+F+F+F',
            'draw': 'F',
            'skip': 'f',
            'angle_increment': 90,
            'turn_left': '+',
            'turn_right': '-',
            'starting_angle': 0,
            'N': 2,
        },
        'Round Koch curve': {
            'rules': [
                'F -> FF-F-F-F-F-F+F',
            ],
            'axiom': 'F-F-F-F',
            'draw': 'F',
            'angle_increment': 90,
            'turn_left': '+',
            'turn_right': '-',
            'starting_angle': 0,
            'N': 4,
        },
    }



if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
