from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from canvas import SimulationCanvas
import sys

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("Network Simulation")
window.resize(800, 600)

layout = QVBoxLayout()
canvas = SimulationCanvas()
layout.addWidget(canvas)
window.setLayout(layout)

# Temp code to add nodes while i figure out some things
canvas.add_node(100, 100, node_type="normal", id="A")
canvas.add_node(250, 100, node_type="special", id="Server-1")
canvas.add_node(400, 150, node_type="normal", id="B")
canvas.add_node(550, 300, node_type="special", id="Gateway")
canvas.add_node(700, 450, node_type="normal", id="C")
canvas.add_node(200, 400, node_type="normal", id="D")
canvas.add_node(350, 350, node_type="special", id="Router-1")

window.show()
sys.exit(app.exec())
