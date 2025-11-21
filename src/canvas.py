from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QMessageBox
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import Qt, QPoint, QTimer
from node import NormalNode, SpecialNode
from connection import Connection
import math

# Important canvas, basically the simulation area
# The point of this is to simulate the world

class SimulationCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.nodes = []
        self.connections = []  # Store all connections
        self.active_signals = []  # Store active signal rings
        self.preview_node = None
        self.positioning_mode = False
        self.dragging = False
        self.drag_offset = QPoint(0, 0)
        self.position_callback = None
        self.cancel_callback = None
        self.save_position_button = None
        self.cancel_position_button = None
        self.selected_node = None  # Currently selected node
        self.sidebar = None  # Reference to sidebar widget
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        # Scale factor: 30 meters = 150 pixels (adjustable)
        # Assuming 1 meter = 5 pixels as default
        self.meter_to_pixel = 5
        self.signal_range_meters = 30
        self.signal_range_pixels = self.signal_range_meters * self.meter_to_pixel
        
        # Animation timer for connections and packets
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animations)
        self.animation_timer.start(16)  # ~60 FPS

    def add_node(self, x, y, node_type="normal", id=None, url=None):
        # Create and add a node by type
        if node_type == "special":
            node = SpecialNode(x, y, id, url)
        else:
            node = NormalNode(x, y, id, url)
        node.canvas_ref = self  # Set canvas reference for signal broadcasting
        self.nodes.append(node)
        self.update()

    def add_node_object(self, node):
        # Add an already-created node object
        node.canvas_ref = self  # Set canvas reference
        self.nodes.append(node)
        self.update()
    
    def create_connection(self, node_a, node_b, delay, receiving_node=None, sending_node=None):
        """Create a connection between two nodes"""
        # Check if connection already exists
        for conn in self.connections:
            if ((conn.node_a == node_a and conn.node_b == node_b) or
                (conn.node_a == node_b and conn.node_b == node_a)):
                # Update delay if different
                if conn.delay != delay:
                    conn.delay = delay
                    self.update()
                    # Refresh sidebar if selected node is involved
                    if self.sidebar and self.selected_node and (self.selected_node == node_a or self.selected_node == node_b):
                        self.sidebar.set_selected_node(self.selected_node, self)
                return conn
        
        # Create new connection with node objects
        connection = Connection(node_a, node_b, delay, receiving_node=receiving_node, sending_node=sending_node)
        self.connections.append(connection)
        
        # Also update node's internal connection tracking (this uses IDs for JSON storage)
        node_a._add_neighbour_entry(node_b.id, node_b.node_type, delay)
        node_b._add_neighbour_entry(node_a.id, node_a.node_type, delay)
        node_a._save_to_json()
        node_b._save_to_json()
        
        # Refresh sidebar if selected node is involved
        if self.sidebar and self.selected_node and (self.selected_node == node_a or self.selected_node == node_b):
            self.sidebar.set_selected_node(self.selected_node, self)
        
        self.update()
        return connection
    
    def _update_animations(self):
        """Update all connection animations and packets"""
        needs_update = False
        
        # Check signal rings for node contact
        if hasattr(self, 'active_signals'):
            for signal_ring in self.active_signals[:]:
                if signal_ring.active and hasattr(signal_ring, 'sender_node'):
                    current_radius = signal_ring.current_size / 2
                    sender = signal_ring.sender_node
                    
                    for node in self.nodes:
                        if node == sender:
                            continue
                        if node not in signal_ring.nodes_contacted:
                            distance = math.sqrt((node.x - sender.x)**2 + (node.y - sender.y)**2)
                            # When signal reaches the node (circle goes over it)
                            if current_radius >= distance:
                                signal_ring.nodes_contacted.append(node)
                                node.receive_signal(sender, distance)
                                needs_update = True
        
        # Update connections
        for connection in self.connections:
            connection.update()
            needs_update = True
        
        # Update sidebar status if node is selected
        if needs_update and self.sidebar:
            self.sidebar.update_status()
        
        if needs_update:
            self.update()
    
    def start_positioning(self, node_type, callback, cancel_callback=None):
        # Start positioning mode with a preview node
        self.positioning_mode = True
        self.position_callback = callback
        self.cancel_callback = cancel_callback
        # Create preview node at center of canvas
        width = max(100, self.width() if self.width() > 0 else 400)
        height = max(100, self.height() if self.height() > 0 else 400)
        center_x = width // 2
        center_y = height // 2
        
        if node_type == "special":
            self.preview_node = SpecialNode(center_x, center_y, None, None)
        else:
            self.preview_node = NormalNode(center_x, center_y, None, None)
        
        # Create save position button, only once
        if self.save_position_button is None:
            self.save_position_button = QPushButton("Save Position", self)
            self.save_position_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    font-size: 14px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            self.save_position_button.clicked.connect(self._save_position)
        
        # Create cancel button, only once
        if self.cancel_position_button is None:
            self.cancel_position_button = QPushButton("Cancel", self)
            self.cancel_position_button.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    font-size: 14px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
            """)
            self.cancel_position_button.clicked.connect(self._cancel_positioning)
        
        # Position buttons at bottom center
        def show_buttons():
            try:
                if self.save_position_button and self.cancel_position_button:
                    self.save_position_button.show()
                    self.cancel_position_button.show()
                    self._update_button_position()
                    self.setFocus()
                    self.update()
            except Exception as e:
                print(f"Error showing positioning buttons: {e}")
                self._exit_positioning()
        
        QTimer.singleShot(10, show_buttons)
    
    def _update_button_position(self):
        # Update the save position button location
        if self.save_position_button and self.cancel_position_button:
            if self.width() <= 0 or self.height() <= 0:
                return
            button_width = 120
            button_height = 40
            spacing = 10
            total_width = button_width * 2 + spacing
            x_start = max(0, (self.width() - total_width) // 2)
            y = max(0, self.height() - button_height - 20)
            
            self.save_position_button.setGeometry(x_start, y, button_width, button_height)
            self.cancel_position_button.setGeometry(x_start + button_width + spacing, y, button_width, button_height)
    
    def _cancel_positioning(self):
        # Cancel positioning mode without saving
        if self.cancel_callback:
            self.cancel_callback()
        self._exit_positioning()
    
    def _save_position(self):
        # Save the current preview node position and exit positioning mode
        if self.preview_node and self.position_callback:
            if self._check_overlap(self.preview_node.x, self.preview_node.y):
                QMessageBox.warning(
                    self,
                    "Overlap Detected",
                    "The node position overlaps with an existing node. Please move it to a different location."
                )
                return
            self.position_callback(self.preview_node.x, self.preview_node.y)
        self._exit_positioning()
    
    def _exit_positioning(self):
        # Exit positioning mode
        self.positioning_mode = False
        self.preview_node = None
        self.dragging = False
        self.position_callback = None
        self.cancel_callback = None
        if self.save_position_button:
            self.save_position_button.hide()
        if self.cancel_position_button:
            self.cancel_position_button.hide()
        self.update()
    
    def _check_overlap(self, x, y, exclude_node=None):
        # Check if a position would overlap with existing nodes
        node_size = 20
        min_distance = node_size * 2  # Minimum distance between nodes
        
        for node in self.nodes:
            if exclude_node and node == exclude_node:
                continue
            distance = math.sqrt((node.x - x)**2 + (node.y - y)**2)
            if distance < min_distance:
                return True
        return False
    
    def mousePressEvent(self, event):
        # Handle mouse press events
        if self.positioning_mode and self.preview_node:
            # Check if click is on the preview node
            distance = math.sqrt(
                (event.position().x() - self.preview_node.x)**2 + 
                (event.position().y() - self.preview_node.y)**2
            )
            if distance <= self.preview_node.size:
                self.dragging = True
                self.drag_offset = QPoint(
                    int(event.position().x() - self.preview_node.x),
                    int(event.position().y() - self.preview_node.y)
                )
        elif event.button() == Qt.LeftButton:
            # Left-click to select node
            clicked_node = self._get_node_at_position(event.position().x(), event.position().y())
            
            # If clicking on empty space, deselect
            if not clicked_node:
                self.selected_node = None
                if self.sidebar:
                    self.sidebar.set_selected_node(None, self)
            else:
                self.selected_node = clicked_node
                # Update sidebar if it exists
                if self.sidebar:
                    self.sidebar.set_selected_node(clicked_node, self)
            
            self.update()
        super().mousePressEvent(event)
    
    def _get_node_at_position(self, x, y):
        """Get the node at the given position, if any"""
        for node in self.nodes:
            distance = math.sqrt((node.x - x)**2 + (node.y - y)**2)
            if distance <= node.size:
                return node
        return None
    
    
    def mouseMoveEvent(self, event):
        # Handle mouse move events for dragging
        if self.positioning_mode and self.dragging and self.preview_node:
            new_x = int(event.position().x() - self.drag_offset.x())
            new_y = int(event.position().y() - self.drag_offset.y())
            
            # Keep within canvas bounds
            new_x = max(self.preview_node.size, min(new_x, self.width() - self.preview_node.size))
            new_y = max(self.preview_node.size, min(new_y, self.height() - self.preview_node.size))
            
            # Allow movement (overlap check is visual only, prevents saving)
            self.preview_node.x = new_x
            self.preview_node.y = new_y
            self.update()
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        # Handle mouse release events
        if self.dragging:
            self.dragging = False
        super().mouseReleaseEvent(event)
    
    def resizeEvent(self, event):
        # Handle resize events
        self._update_button_position()
        super().resizeEvent(event)

    def paintEvent(self, event):
        # Paint the canvas
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(240, 240, 240))

        # Draw connections first (so they appear behind nodes)
        for connection in self.connections:
            connection.draw(painter)
        
        # Draw active signal rings
        if hasattr(self, 'active_signals'):
            for signal_ring in self.active_signals:
                if signal_ring.active:
                    painter.save()
                    painter.setOpacity(0.5)  # Half transparent
                    signal_ring.draw(painter)
                    painter.restore()

        # Draw existing nodes
        for node in self.nodes:
            node.draw(painter)
        
        # Highlight selected node
        if self.selected_node:
            painter.save()
            painter.setPen(QColor(0, 150, 255))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(
                int(self.selected_node.x - self.selected_node.size - 3),
                int(self.selected_node.y - self.selected_node.size - 3),
                int((self.selected_node.size + 3) * 2),
                int((self.selected_node.size + 3) * 2)
            )
            painter.restore()
        
        # Draw preview node if in positioning mode
        if self.positioning_mode and self.preview_node:
            painter.save()
            painter.setOpacity(0.7)
            self.preview_node.draw(painter)
            painter.restore()
            
            if self._check_overlap(self.preview_node.x, self.preview_node.y):
                painter.setPen(QColor(255, 0, 0))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(
                    int(self.preview_node.x - self.preview_node.size),
                    int(self.preview_node.y - self.preview_node.size),
                    int(self.preview_node.size * 2),
                    int(self.preview_node.size * 2)
                )
