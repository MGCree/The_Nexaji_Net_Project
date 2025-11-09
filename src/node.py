import os
import json
import math
from PySide6.QtGui import QPainter, QColor, QPolygon
from PySide6.QtCore import QPoint, Qt
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPen

class Connection:
    # Represents a link between two nodes with a given delay.
    def __init__(self, node_a_id, node_b_id, delay):
        self.node_a_id = node_a_id
        self.node_b_id = node_b_id
        self.delay = delay

    def to_dict(self):
        return {
            "node_a": self.node_a_id,
            "node_b": self.node_b_id,
            "delay": self.delay,
        }

# Main Node class that holds the info and functions nodes share

class Node:
    def __init__(self, x, y, id=None, delay=0):
        self.id = id
        self.x = x
        self.y = y
        self.size = 20
        self.node_type = "base"
        self.delay = delay
        self.neighbours = [] # list of nearby nodes (temporary while i figure out connection and stuff)

        # Creates folder and JSON of the specific node
        self._setup_storage()

    # In a real application of this this function would not be needed
    def _setup_storage(self):
        base_dir = os.path.join(os.path.dirname(__file__), "Nodes")
        node_dir = os.path.join(base_dir, self.id or "Unnamed")
        os.makedirs(node_dir, exist_ok=True)
        self.file_path = os.path.join(node_dir, "data.json")

        if not os.path.exists(self.file_path):
            self._save_to_json()

    def _save_to_json(self):
        data = {
            "id": self.id,
            "type": self.node_type,
            "x": self.x,
            "y": self.y,
            "delay": self.delay,
            "neighbours": self.neighbours,
        }
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=4)

    def add_connection(self, other_node, delay):
        # Add a connection between this node and another, with delay.
        # Add to self
        self._add_neighbour_entry(other_node.id, other_node.node_type, delay)
        # Add to other
        other_node._add_neighbour_entry(self.id, self.node_type, delay)
        # Save both
        self._save_to_json()
        other_node._save_to_json()
        # Return a Connection object
        return Connection(self.id, other_node.id, delay)

    def _add_neighbour_entry(self, neighbour_id, neighbour_type, delay):
        existing = next((n for n in self.neighbours if n["id"] == neighbour_id), None)
        if existing:
            existing.update({"delay": delay, "type": neighbour_type})
        else:
            self.neighbours.append({"id": neighbour_id, "delay": delay, "type": neighbour_type})

    def evolve(self):
        # A function for evolving a node into a special node
        return SpecialNode(self.x, self.y, id=self.id, delay=self.delay)

    def unevolve(self):
        # A function for devolving a special node into a normal
        return NormalNode(self.x, self.y, id=self.id, delay=self.delay)

    def call():
        # Unfinished function for createing a ConnectionRing at the node
        print("call")

# A Normal Node representing a typical router type device in a home or business
class NormalNode(Node):
    def __init__(self, x, y, id=None, delay=5):
        super().__init__(x, y, id, delay)
        self.node_type = "normal"
        self._save_to_json()

    def draw(self, painter: QPainter, delay=None):
        effective_delay = delay if delay is not None else self.delay
        painter.setBrush(QColor(100, 180, 255))
        painter.drawRect(
            self.x - self.size / 2,
            self.y - self.size / 2,
            self.size,
            self.size,
        )
        painter.drawText(self.x - 10, self.y - 10, f"{effective_delay}ms")

# A special Node representing the same router type device but with a server running a service
class SpecialNode(Node):
    def __init__(self, x, y, id=None, delay=2):
        super().__init__(x, y, id, delay)
        self.node_type = "special"
        self._save_to_json()

    def draw(self, painter: QPainter, delay=None):
        effective_delay = delay if delay is not None else self.delay
        painter.setBrush(QColor(255, 180, 80))
        points = []
        for i in range(6):
            angle = math.radians(60 * i)
            px = self.x + self.size * math.cos(angle)
            py = self.y + self.size * math.sin(angle)
            points.append(QPoint(int(px), int(py)))
        polygon = QPolygon(points)
        painter.drawPolygon(polygon)
        painter.drawText(self.x - 10, self.y - 10, f"{effective_delay}ms")

""" 
Connection Ring simulating the range of a call for connection from the node, nodes connect to the network by sending a signal with a request
with a transmiter and this ring symbolizes that signal being sent
"""
class ConnectionRing:
    def __init__(self, x, y, max_size=60, color=QColor(0, 120, 255)):
        self.x = x
        self.y = y
        self.max_size = max_size
        self.current_size = 5       # starts small
        self.growth_speed = 2       # pixels per frame
        self.color = color
        self.active = True

        # Timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_wave)
        self.timer.start(30)  # about 33 FPS (smooth enough for now)

    def _update_wave(self):
        """Increase size, reset when reaching the max."""
        if not self.active:
            return
        self.current_size += self.growth_speed
        if self.current_size >= self.max_size:
            self.current_size = 5  # restart the wave
        # Ask the widget to repaint (the parent canvas will call update)
        if hasattr(self, "parent_widget") and self.parent_widget:
            self.parent_widget.update()

    def attach_to_canvas(self, canvas_widget):
        self.parent_widget = canvas_widget

    def draw(self, painter: QPainter):
        # Draw a fading ring expanding from the center.
        radius = self.current_size / 2

        # Transparency decreases as it expands (fade out)
        alpha = max(0, 255 - int((self.current_size / self.max_size) * 255))
        color = QColor(self.color)
        color.setAlpha(alpha)

        pen = QPen(color, 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        painter.drawEllipse(
            int(self.x - radius),
            int(self.y - radius),
            int(self.current_size),
            int(self.current_size),
        )
