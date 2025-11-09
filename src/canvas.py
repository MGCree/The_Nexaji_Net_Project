from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor
from node import NormalNode, SpecialNode

# Important canvas, basically the simulation area
# The point of this is to simulate the world

class SimulationCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.nodes = []

    def add_node(self, x, y, node_type="normal", id=None):
        """Create and add a node by type."""
        if node_type == "special":
            node = SpecialNode(x, y, id)
        else:
            node = NormalNode(x, y, id)
        self.nodes.append(node)
        self.update()

    def add_node_object(self, node):
        """Add an already-created node object."""
        self.nodes.append(node)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(240, 240, 240))

        for node in self.nodes:
            node.draw(painter)
