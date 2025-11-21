import os
import json
import math
from PySide6.QtGui import QPainter, QColor, QPolygon
from PySide6.QtCore import QPoint, Qt
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPen
from connection import Connection

class Node:
    def __init__(self, x, y, id=None, url=None):
        self.id = id
        self.x = x
        self.y = y
        self.size = 20
        self.node_type = "base"
        self.url = url  # URL for use to access a "site" instead of remembering the id
        self.neighbours = [] # list of nearby nodes
        self.listening = True  # Node is always listening for signals
        self.canvas_ref = None  # Reference to canvas for signal broadcasting

        # Creates folder and JSON of the specific node
        self._setup_storage()
        
        # Load discovered services
        self._load_services_from_json()

    # In a real application of this this function would not be needed
    def _setup_storage(self):
        base_dir = os.path.join(os.path.dirname(__file__), "Nodes")
        node_dir = os.path.join(base_dir, self.id or "Unnamed")
        os.makedirs(node_dir, exist_ok=True)
        self.file_path = os.path.join(node_dir, "data.json")
        self.services_file_path = os.path.join(node_dir, "services.json")  # Second JSON file for services

        if not os.path.exists(self.file_path):
            self._save_to_json()
        
        # Initialize services file if it doesn't exist
        if not os.path.exists(self.services_file_path):
            self._save_services_to_json()

    def _save_to_json(self):
        data = {
            "id": self.id,
            "type": self.node_type,
            "x": self.x,
            "y": self.y,
            "url": self.url,
            "neighbours": self.neighbours,
        }
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=4)
    
    def _save_services_to_json(self):
        """Save discovered services to the second JSON file"""
        if not hasattr(self, 'discovered_services'):
            self.discovered_services = []
        
        with open(self.services_file_path, "w") as f:
            json.dump(self.discovered_services, f, indent=4)
    
    def _load_services_from_json(self):
        """Load discovered services from the second JSON file"""
        if os.path.exists(self.services_file_path):
            try:
                with open(self.services_file_path, "r") as f:
                    content = f.read().strip()
                    if not content or content == "[]":
                        self.discovered_services = []
                    else:
                        data = json.loads(content)
                        self.discovered_services = data if isinstance(data, list) else []
            except (json.JSONDecodeError, ValueError):
                self.discovered_services = []
        else:
            self.discovered_services = []
    
    def has_empty_services(self):
        """Check if the services.json file is empty or has no services"""
        if not hasattr(self, 'discovered_services'):
            self._load_services_from_json()
        return len(self.discovered_services) == 0
    
    def share_services_with_node(self, other_node):
        """
        Share all discovered services with another node.
        Sends each service as a separate packet with path starting from this node.
        Only sends services that the other node doesn't already have.
        """
        if not hasattr(self, 'discovered_services'):
            self._load_services_from_json()
        
        if len(self.discovered_services) == 0:
            return False
        
        if not self.canvas_ref or not hasattr(self.canvas_ref, 'connections'):
            return False
        
        # Find connection to the other node
        connection = None
        for conn in self.canvas_ref.connections:
            if (conn.node_a == self and conn.node_b == other_node) or \
               (conn.node_b == self and conn.node_a == other_node):
                connection = conn
                break
        
        if not connection or connection.state != "active":
            return False  # No active connection
        
        # Load other node's services to check what they already have
        if not hasattr(other_node, 'discovered_services'):
            other_node._load_services_from_json()
        
        other_services = {s.get("service_id") for s in other_node.discovered_services}
        
        # Send each service as a separate packet, but only if they don't already have it
        sent_count = 0
        for service in self.discovered_services:
            service_id = service.get("service_id")
            
            # Skip if the other node already has this service
            if service_id in other_services:
                continue
            
            # Create a copy of the service data with path starting from this node
            # The receiving node will add itself to the path
            service_data = {
                "service_id": service_id,
                "service_url": service.get("service_url", ""),
                "service_type": service.get("service_type"),
                "path": [self.id],  # Path starts from this node
                "total_delay": 0  # Will be updated when received
            }
            
            if self.send_packet(other_node.id, "SERVICE", service_data):
                sent_count += 1
        
        return sent_count > 0

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
        return SpecialNode(self.x, self.y, id=self.id, url=self.url)

    def unevolve(self):
        # A function for devolving a special node into a normal
        return NormalNode(self.x, self.y, id=self.id, url=self.url)

    def call():
        # Unfinished function for creating a ConnectionRing at the node
        print("call")
    
    def send_packet(self, destination_id, value="", packet_data=None):
        """
        Send a packet to another node through a connection.
        Finds the connection to the destination node and sends the packet.
        Returns True if packet was sent, False otherwise.
        packet_data: Optional dictionary with additional packet information (for service discovery)
        """
        if not self.canvas_ref or not hasattr(self.canvas_ref, 'connections'):
            return False
        
        # Find connection to destination node
        """
            Will add algorithms that actually find paths to location later
        """
        target_connection = None
        for conn in self.canvas_ref.connections:
            # Check if this connection involves current node and the destination
            other_node = None
            if conn.node_a == self:
                if hasattr(conn.node_b, 'id') and conn.node_b.id == destination_id:
                    other_node = conn.node_b
                elif conn.node_b == destination_id:  # In case it's stored as ID
                    # Need to find the actual node
                    for node in self.canvas_ref.nodes:
                        if node.id == destination_id:
                            other_node = node
                            break
            elif conn.node_b == self:
                if hasattr(conn.node_a, 'id') and conn.node_a.id == destination_id:
                    other_node = conn.node_a
                elif conn.node_a == destination_id:
                    for node in self.canvas_ref.nodes:
                        if node.id == destination_id:
                            other_node = node
                            break
            
            if other_node:
                target_connection = conn
                break
        
        if not target_connection:
            return False  # No connection to destination
        
        # Use connection's send_packet method
        return target_connection.send_packet(self, destination_id, value, packet_data)
    
    def send_service_discovery(self, service_type):
        """
        Send service discovery packets to all connected nodes.
        Only special nodes can send service discovery.
        """
        if self.node_type != "special":
            return False
        
        if not self.canvas_ref or not hasattr(self.canvas_ref, 'connections'):
            return False
        
        # Create service discovery packet data
        service_data = {
            "service_id": self.id,
            "service_url": self.url or "",
            "service_type": service_type,
            "path": [self.id],  # Start path with this node's ID
            "total_delay": 0  # Start with 0 delay
        }
        
        # Send to all connected nodes
        sent_count = 0
        for conn in self.canvas_ref.connections:
            if conn.state == "active":  # Only send through active connections
                other_node = None
                if conn.node_a == self:
                    other_node = conn.node_b
                elif conn.node_b == self:
                    other_node = conn.node_a
                
                if other_node:
                    if self.send_packet(other_node.id, "SERVICE", service_data):
                        sent_count += 1
        
        return sent_count > 0
    
    def receive_service_packet(self, service_data, sender_node, connection_delay):
        """
        Handle receiving a service discovery packet.
        Store the service info and forward to other connected nodes.
        """
        if not hasattr(self, 'discovered_services'):
            self.discovered_services = []
        
        # Update path and delay
        service_data = service_data.copy()  # Make a copy to avoid modifying original
        service_data["path"] = service_data.get("path", []) + [self.id]
        service_data["total_delay"] = service_data.get("total_delay", 0) + connection_delay
        
        # Check if we already have this service (same service_id and path length)
        # If we have a shorter path, update it
        existing_index = None
        for i, existing in enumerate(self.discovered_services):
            if existing.get("service_id") == service_data.get("service_id"):
                # Keep the one with shorter path or lower delay
                if len(service_data["path"]) < len(existing.get("path", [])) or \
                   service_data["total_delay"] < existing.get("total_delay", float('inf')):
                    existing_index = i
                else:
                    # Already have a better path, don't update
                    return
                break
        
        # Add or update service
        if existing_index is not None:
            self.discovered_services[existing_index] = service_data
        else:
            self.discovered_services.append(service_data)
        
        # Save to JSON
        self._save_services_to_json()
        
        # Forward to all connected nodes except the sender
        # But only forward to nodes that don't already have this service
        if not self.canvas_ref or not hasattr(self.canvas_ref, 'connections'):
            return
        
        service_id = service_data.get("service_id")
        
        for conn in self.canvas_ref.connections:
            if conn.state == "active":  # Only forward through active connections
                other_node = None
                if conn.node_a == self:
                    other_node = conn.node_b
                elif conn.node_b == self:
                    other_node = conn.node_a
                
                if other_node and other_node != sender_node:
                    # Check if the target node already has this service
                    # Only forward if they don't have it or if we have a better path
                    should_forward = True
                    
                    if hasattr(other_node, 'discovered_services'):
                        # Load services if not loaded
                        if not hasattr(other_node, '_services_loaded'):
                            other_node._load_services_from_json()
                            other_node._services_loaded = True
                        
                        # Check if target node already has this service
                        for existing_service in other_node.discovered_services:
                            if existing_service.get("service_id") == service_id:
                                # They already have it - check if our path is better
                                existing_path_len = len(existing_service.get("path", []))
                                existing_delay = existing_service.get("total_delay", float('inf'))
                                new_path_len = len(service_data.get("path", []))
                                new_delay = service_data.get("total_delay", 0)
                                
                                # Only forward if we have a better path (shorter or lower delay)
                                if new_path_len >= existing_path_len and new_delay >= existing_delay:
                                    should_forward = False
                                break
                    
                    if should_forward:
                        # Forward the packet
                        self.send_packet(other_node.id, "SERVICE", service_data)

    def send_signal(self, signal_range_pixels=150):
        """
        Send a connection signal that expands in a circle.
        signal_range_pixels: The radius in pixels (scaled from 30 meters)
        """
        if not self.canvas_ref:
            return
        
        # Create a signal ring that expands
        signal_ring = ConnectionRing(self.x, self.y, max_size=signal_range_pixels * 2, color=QColor(0, 120, 255))
        signal_ring.attach_to_canvas(self.canvas_ref)
        signal_ring.sender_node = self  # Store reference to sender
        signal_ring.range_pixels = signal_range_pixels
        signal_ring.nodes_contacted = []  # Track which nodes have been contacted
        
        # Store reference in canvas for drawing
        if not hasattr(self.canvas_ref, 'active_signals'):
            self.canvas_ref.active_signals = []
        self.canvas_ref.active_signals.append(signal_ring)
        
        # Disconnect the original update and connect the enhanced version
        try:
            signal_ring.timer.timeout.disconnect()
        except:
            pass  # Might not be connected yet
        
        def update_with_contact_check():
            # Original update logic
            if not signal_ring.active:
                return
            signal_ring.current_size += signal_ring.growth_speed
            if signal_ring.current_size >= signal_ring.max_size:
                signal_ring.current_size = 5  # restart the wave
            
            # Check if signal has reached any nodes
            if self.canvas_ref and hasattr(self.canvas_ref, 'nodes'):
                current_radius = signal_ring.current_size / 2
                for node in self.canvas_ref.nodes:
                    if node == self:
                        continue
                    if node not in signal_ring.nodes_contacted:
                        distance = math.sqrt((node.x - self.x)**2 + (node.y - self.y)**2)
                        # When signal reaches the node (circle goes over it)
                        # Account for node size by checking if radius reaches node center
                        if current_radius >= distance:
                            signal_ring.nodes_contacted.append(node)
                            node.receive_signal(self, distance)
            
            # Ask the widget to repaint
            if hasattr(signal_ring, "parent_widget") and signal_ring.parent_widget:
                signal_ring.parent_widget.update()
        
        signal_ring.timer.timeout.connect(update_with_contact_check)
        
        # Remove signal after animation completes (one full cycle)
        def remove_signal():
            if hasattr(self.canvas_ref, 'active_signals') and signal_ring in self.canvas_ref.active_signals:
                signal_ring.active = False
                signal_ring.timer.stop()
                self.canvas_ref.active_signals.remove(signal_ring)
                self.canvas_ref.update()
        
        # Calculate time for one full cycle
        cycle_time = (signal_range_pixels * 2 - 5) / signal_ring.growth_speed * 30  # milliseconds
        QTimer.singleShot(int(cycle_time), remove_signal)
    
    
    def receive_signal(self, sender_node, distance):
        """
        Receive a signal from another node and perform handshake.
        This is called when a signal is detected within range.
        """
        if not self.listening:
            return
        
        # Check if connection already exists
        existing_connection = None
        if hasattr(self.canvas_ref, 'connections'):
            for conn in self.canvas_ref.connections:
                if ((conn.node_a == self and conn.node_b == sender_node) or
                    (conn.node_a == sender_node and conn.node_b == self)):
                    existing_connection = conn
                    break
        
        # If no connection exists, establish one
        if not existing_connection:
            # Calculate delay based on distance (1ms per 10 pixels, minimum 1ms)
            delay = max(1, int(distance / 10))
            
            # Create connection through canvas with receiving and sending node info
            if self.canvas_ref:
                self.canvas_ref.create_connection(self, sender_node, delay, receiving_node=self, sending_node=sender_node)
                
                # After establishing a connection, this node should broadcast its own signal
                # to connect with other nearby nodes. Use a small delay to avoid signal collision.
                def broadcast_own_signal():
                    if self.canvas_ref and self.listening:
                        self.send_signal(self.canvas_ref.signal_range_pixels)
                
                # Delay the signal broadcast by 500ms to let the current signal finish
                QTimer.singleShot(500, broadcast_own_signal)

# A Normal Node representing a typical router type device in a home or business
class NormalNode(Node):
    def __init__(self, x, y, id=None, url=None):
        super().__init__(x, y, id, url)
        self.node_type = "normal"
        self._save_to_json()

    def draw(self, painter: QPainter):
        painter.setBrush(QColor(100, 180, 255))
        painter.drawRect(
            self.x - self.size / 2,
            self.y - self.size / 2,
            self.size,
            self.size,
        )
        # Draw node ID if available
        if self.id:
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(self.x - 10, self.y - 10, self.id)

# A special Node representing the same router type device but with a server running a service
class SpecialNode(Node):
    def __init__(self, x, y, id=None, url=None):
        super().__init__(x, y, id, url)
        self.node_type = "special"
        self._save_to_json()

    def draw(self, painter: QPainter):
        painter.setBrush(QColor(255, 180, 80))
        points = []
        for i in range(6):
            angle = math.radians(60 * i)
            px = self.x + self.size * math.cos(angle)
            py = self.y + self.size * math.sin(angle)
            points.append(QPoint(int(px), int(py)))
        polygon = QPolygon(points)
        painter.drawPolygon(polygon)
        # Draw node ID if available
        if self.id:
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(self.x - 10, self.y - 10, self.id)

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
        # Draw a fading filled circle expanding from the center.
        radius = self.current_size / 2

        # Transparency decreases as it expands (fade out)
        alpha = max(0, 128 - int((self.current_size / self.max_size) * 128))  # Max 50% opacity
        color = QColor(self.color)
        color.setAlpha(alpha)

        pen = QPen(color, 1)
        painter.setPen(pen)
        painter.setBrush(color)

        painter.drawEllipse(
            int(self.x - radius),
            int(self.y - radius),
            int(self.current_size),
            int(self.current_size),
        )
