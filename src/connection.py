from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt

"""
This Class symbolizes a "connection" between nodes, showing which nodes can communicate between each other and used to show the delay in data
sent and to visualise the network being connected

In the future this will have animations to show packets of data being sent and the future algorithms working.

One such algorithm will be used to find the shortest path to another node.
"""
class Connection:
    def __init__(self, node_a, node_b, delay=0):
        self.node_a = node_a
        self.node_b = node_b
        self.delay = delay

    def draw(self, painter: QPainter):
        # Draw a line between node_a and node_b with delay label.
        pen = QPen(QColor(120, 120, 120), 2)
        painter.setPen(pen)
        painter.drawLine(self.node_a.x, self.node_a.y, self.node_b.x, self.node_b.y)

        # Draw the delay text near the middle of the line
        mid_x = (self.node_a.x + self.node_b.x) / 2
        mid_y = (self.node_a.y + self.node_b.y) / 2
        painter.setPen(QColor(80, 80, 80))
        painter.drawText(mid_x + 5, mid_y - 5, f"{self.delay}ms")
