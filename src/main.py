from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout
from canvas import SimulationCanvas
from control_bar import ControlBar
from node_sidebar import NodeSidebar
from packet_sidebar import PacketSidebar
import sys

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("Network Simulation")
window.resize(1200, 600)

# Main vertical layout
main_layout = QVBoxLayout()
main_layout.setContentsMargins(0, 0, 0, 0)
main_layout.setSpacing(0)

# Horizontal layout for sidebars and canvas
content_layout = QHBoxLayout()
content_layout.setContentsMargins(0, 0, 0, 0)
content_layout.setSpacing(0)

# Add left sidebar (packet controls)
left_sidebar = PacketSidebar()
content_layout.addWidget(left_sidebar)

# Add canvas
canvas = SimulationCanvas()
content_layout.addWidget(canvas)

# Add control bar at the top
control_bar = ControlBar()
control_bar.set_canvas(canvas)
main_layout.addWidget(control_bar)

# Add right sidebar (node info)
sidebar = NodeSidebar()
content_layout.addWidget(sidebar)

# Connect canvas and sidebars
canvas.sidebar = sidebar
canvas.left_sidebar = left_sidebar

main_layout.addLayout(content_layout)

window.setLayout(main_layout)

# Load nodes from storage on launch
canvas.load_nodes_from_storage()

window.show()
sys.exit(app.exec())
