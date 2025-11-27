from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QTimer
from packet import Packet
import math

"""
This Class symbolizes a "connection" between nodes, showing which nodes can communicate between each other and used to show the delay in data
sent and to visualise the network being connected

In the future this will have animations to show packets of data being sent and the future algorithms working.

One such algorithm will be used to find the shortest path to another node.
"""
class Connection:
    # Connection states
    HANDSHAKING = "handshaking"
    ESTABLISHED = "established"
    ACTIVE = "active"
    
    def __init__(self, node_a, node_b, delay=0, type="wireless", receiving_node=None, sending_node=None):
        # node_a and node_b can be either Node objects or node IDs
        self.node_a = node_a
        self.node_b = node_b
        self.delay = delay  # Delay in milliseconds
        self.type = type
        self.state = Connection.HANDSHAKING
        self.receiving_node = receiving_node  # Node that received the signal
        self.sending_node = sending_node  # Node that sent the signal
        self.packets = []  # List of active packets
        self.handshake_complete = False
        self.line_progress = 0.0  # 0.0 to 1.0 for drawing line animation
        self.line_speed = 0.03  # How fast the line draws
        self.handshake_start_time = None
        self.establishment_time = None  # When connection was established
        self.last_packet_time = None  # When last packet was sent (for delay enforcement)
        self.first_packet_sent = False  # Track if first handshake packet has been sent
        self.first_packet_complete = False  # Track if first handshake packet has completed
        self.services_shared = False  # Track if services have been shared when connection became active
        self.last_activity_time = None  # Track last packet activity for TTL
        self.ttl_duration = 120000  # 2 minutes in milliseconds
        self.is_service_connection = False  # Track if this is a service connection (yellow when active)
    
    def update(self):
        """Update connection state and animations"""
        if self.state == Connection.HANDSHAKING:
            # Animate line drawing from receiving to sending node
            if self.line_progress < 1.0:
                self.line_progress += self.line_speed
                if self.line_progress >= 1.0:
                    self.line_progress = 1.0
                    # Start handshake packets
                    self._start_handshake()
            
            # Update packets
            packets_to_remove = []
            for packet in self.packets:
                completed = packet.update()
                if completed:
                    # Check if this was the first handshake packet completing BEFORE removing it
                    is_first_packet = (not self.first_packet_complete and 
                                      self.receiving_node and 
                                      packet.source_node == self.receiving_node)
                    packets_to_remove.append(packet)
                    
                    if is_first_packet:
                        self.first_packet_complete = True
                        # Immediately send second packet
                        self._send_second_handshake_packet()
            
            # Remove completed packets
            for packet in packets_to_remove:
                if packet in self.packets:
                    self.packets.remove(packet)
            
            # Check if handshake is complete (both packets sent and received)
            if self.handshake_complete and len(self.packets) == 0:
                self.state = Connection.ESTABLISHED
                from PySide6.QtCore import QDateTime
                self.establishment_time = QDateTime.currentMSecsSinceEpoch()
        
        elif self.state == Connection.ESTABLISHED:
            # After 5 seconds, transition to active
            if self.establishment_time:
                from PySide6.QtCore import QDateTime
                elapsed = QDateTime.currentMSecsSinceEpoch() - self.establishment_time
                if elapsed >= 5000:  # 5 seconds
                    self.state = Connection.ACTIVE
                    self.last_activity_time = QDateTime.currentMSecsSinceEpoch()
                    # When connection becomes active, check and share services (only once)
                    if not self.services_shared:
                        self._check_and_share_services()
                        self.services_shared = True
            
            # Update packets during established state
            packets_to_remove = []
            for packet in self.packets:
                if packet.update():
                    packets_to_remove.append(packet)
                    # Handle packet arrival
                    self._handle_packet_arrival(packet)
            for packet in packets_to_remove:
                if packet in self.packets:
                    self.packets.remove(packet)
        
        elif self.state == Connection.ACTIVE:
            # Update packets during active state
            packets_to_remove = []
            for packet in self.packets:
                if packet.update():
                    packets_to_remove.append(packet)
                    # Handle packet arrival
                    self._handle_packet_arrival(packet)
                    # Reset TTL timer on packet activity
                    from PySide6.QtCore import QDateTime
                    self.last_activity_time = QDateTime.currentMSecsSinceEpoch()
            for packet in packets_to_remove:
                if packet in self.packets:
                    self.packets.remove(packet)
            
            # Check TTL - close connection if no activity for 2 minutes
            if self.last_activity_time:
                from PySide6.QtCore import QDateTime
                current_time = QDateTime.currentMSecsSinceEpoch()
                elapsed = current_time - self.last_activity_time
                if elapsed >= self.ttl_duration:
                    # Connection timed out, close it
                    self.state = Connection.HANDSHAKING  # Reset to handshaking (effectively closed)
                    self.handshake_complete = False
                    self.first_packet_sent = False
                    self.first_packet_complete = False
                    self.line_progress = 0.0
                    self.last_activity_time = None
    
    def _check_and_share_services(self):
        """Check if nodes need to share services when connection becomes active"""
        if not self.node_a or not self.node_b:
            return
        
        # Check if nodes have empty services
        node_a_empty = hasattr(self.node_a, 'has_empty_services') and self.node_a.has_empty_services()
        node_b_empty = hasattr(self.node_b, 'has_empty_services') and self.node_b.has_empty_services()
        
        # If one has services and the other doesn't, share them
        if node_a_empty and not node_b_empty:
            # Node B has services, share with Node A
            if hasattr(self.node_b, 'share_services_with_node'):
                self.node_b.share_services_with_node(self.node_a)
        elif node_b_empty and not node_a_empty:
            # Node A has services, share with Node B
            if hasattr(self.node_a, 'share_services_with_node'):
                self.node_a.share_services_with_node(self.node_b)
    
    def _handle_packet_arrival(self, packet):
        """Handle when a packet reaches its destination"""
        if hasattr(packet, 'target_node') and hasattr(packet, 'source_node_obj'):
            target_node = packet.target_node
            source_node = packet.source_node_obj
            
            # Reset TTL timer on any packet activity
            from PySide6.QtCore import QDateTime
            self.last_activity_time = QDateTime.currentMSecsSinceEpoch()
            
            # Handle service discovery packets
            if packet.value == "SERVICE" and hasattr(packet, 'packet_data'):
                if hasattr(target_node, 'receive_service_packet'):
                    target_node.receive_service_packet(packet.packet_data, source_node, self.delay)
            
            # Handle connection request packets
            elif packet.value == "CONNECTION_REQUEST" and hasattr(packet, 'packet_data'):
                if hasattr(target_node, 'handle_connection_request'):
                    target_node.handle_connection_request(packet.packet_data, source_node)
            
            # Handle connection response packets
            elif packet.value == "CONNECTION_RESPONSE" and hasattr(packet, 'packet_data'):
                if hasattr(target_node, 'handle_connection_response'):
                    target_node.handle_connection_response(packet.packet_data, source_node)
    
    def _start_handshake(self):
        """Start the handshake process by sending first packet from receiving node to sending node"""
        if not self.receiving_node or not self.sending_node:
            return
        
        # Only send first packet once
        if self.first_packet_sent:
            return
        
        # Use node's send_packet method to send SYN packet
        if self.receiving_node.send_packet(self.sending_node.id, "SYN"):
            self.first_packet_sent = True
    
    def _send_second_handshake_packet(self):
        """Send second packet from sending node to receiving node"""
        if not self.receiving_node or not self.sending_node:
            return
        
        # Don't send if already sent
        if self.handshake_complete:
            return
        
        # Use node's send_packet method to send ACK packet
        if self.sending_node.send_packet(self.receiving_node.id, "ACK"):
            self.handshake_complete = True
    
    def draw(self, painter: QPainter):
        # Draw a line between node_a and node_b with delay label.
        # Handle both node objects and node IDs
        if hasattr(self.node_a, 'x'):
            x1, y1 = self.node_a.x, self.node_a.y
        else:
            # If it's an ID, we can't draw without node reference
            return
            
        if hasattr(self.node_b, 'x'):
            x2, y2 = self.node_b.x, self.node_b.y
        else:
            return
        
        # Determine which node is receiving and which is sending for line direction
        if self.receiving_node and self.sending_node:
            if self.receiving_node == self.node_a:
                recv_x, recv_y = x1, y1
                send_x, send_y = x2, y2
            else:
                recv_x, recv_y = x2, y2
                send_x, send_y = x1, y1
        else:
            # Fallback to default
            recv_x, recv_y = x1, y1
            send_x, send_y = x2, y2
        
        # Draw line based on state and progress
        if self.state == Connection.HANDSHAKING:
            # Draw red line animating from receiving to sending node
            if self.line_progress > 0:
                # Calculate current line end point
                current_x = recv_x + (send_x - recv_x) * self.line_progress
                current_y = recv_y + (send_y - recv_y) * self.line_progress
                
                pen = QPen(QColor(255, 0, 0), 3)  # Red, thicker
                painter.setPen(pen)
                painter.drawLine(recv_x, recv_y, current_x, current_y)
        elif self.state == Connection.ESTABLISHED:
            # Draw red line (full)
            pen = QPen(QColor(255, 0, 0), 3)
            painter.setPen(pen)
            painter.drawLine(recv_x, recv_y, send_x, send_y)
        else:  # ACTIVE
            # Draw line based on connection type
            if len(self.packets) > 0:
                # Green when packets are being transmitted (all connections)
                pen = QPen(QColor(0, 200, 0), 3)
            else:
                # Service connections are yellow when idle, regular connections are black
                if self.is_service_connection:
                    pen = QPen(QColor(255, 200, 0), 3)  # Yellow for service connections
                else:
                    pen = QPen(QColor(0, 0, 0), 3)  # Black for regular connections
            painter.setPen(pen)
            painter.drawLine(recv_x, recv_y, send_x, send_y)

        # Draw the text centered on the line
        mid_x = (recv_x + send_x) / 2
        mid_y = (recv_y + send_y) / 2
        
        # Calculate perpendicular offset to place text above the line
        dx = send_x - recv_x
        dy = send_y - recv_y
        length = math.sqrt(dx*dx + dy*dy)
        if length > 0:
            # Perpendicular vector (rotated 90 degrees)
            perp_x = -dy / length * 15  # 15 pixels offset
            perp_y = dx / length * 15
        else:
            perp_x = 0
            perp_y = -15
        
        text_x = mid_x + perp_x
        text_y = mid_y + perp_y
        
        if self.state == Connection.HANDSHAKING:
            painter.setPen(QColor(255, 0, 0))
            painter.setFont(painter.font())
            text_rect = painter.fontMetrics().boundingRect("Handshake in progress...")
            painter.drawText(int(text_x - text_rect.width() / 2), int(text_y), "Handshake in progress...")
        elif self.state == Connection.ESTABLISHED:
            painter.setPen(QColor(255, 0, 0))
            text_rect = painter.fontMetrics().boundingRect("Connection established")
            painter.drawText(int(text_x - text_rect.width() / 2), int(text_y), "Connection established")
        else:  # ACTIVE
            # Text color matches line color
            if len(self.packets) > 0:
                painter.setPen(QColor(0, 150, 0))  # Green text when packets active
            else:
                if self.is_service_connection:
                    painter.setPen(QColor(200, 150, 0))  # Orange text for service connections when idle
                else:
                    painter.setPen(QColor(0, 0, 0))  # Black text for regular connections when idle
            delay_text = f"{self.delay}ms"
            text_rect = painter.fontMetrics().boundingRect(delay_text)
            painter.drawText(int(text_x - text_rect.width() / 2), int(text_y), delay_text)
        
        # Draw packets
        for packet in self.packets:
            # Determine target coordinates based on packet destination
            if packet.source_node == self.node_a:
                target_x, target_y = x2, y2
            else:
                target_x, target_y = x1, y1
            packet.draw(painter, target_x, target_y)

    def send_data(self, data, target_node):
        # Send data to a target node
        if self.type == "wireless":
            # Wireless data is sent as a signal
            target_node.receive_data(data)
        else:
            # Wired data is sent as a physical connection
            target_node.receive_data(data)
    
    def send_packet(self, source_node, destination_id, value="", packet_data=None):
        """Send a packet through this connection, respecting delay"""
        # Allow packets during handshake and active states
        # Also allow connection request/response packets during established state
        if self.state not in [Connection.HANDSHAKING, Connection.ESTABLISHED, Connection.ACTIVE]:
            return False
        
        # Connection requests/responses can be sent during established state
        if self.state == Connection.ESTABLISHED and value not in ["CONNECTION_REQUEST", "CONNECTION_RESPONSE"]:
            return False
        
        # Determine target node
        if source_node == self.node_a:
            target_node = self.node_b
        elif source_node == self.node_b:
            target_node = self.node_a
        else:
            return False  # Source node not part of this connection
        
        # Check if destination matches
        if hasattr(target_node, 'id') and target_node.id != destination_id:
            return False  # Destination doesn't match
        
        # For active connections, check delay
        if self.state == Connection.ACTIVE:
            from PySide6.QtCore import QDateTime
            current_time = QDateTime.currentMSecsSinceEpoch()
            
            if self.last_packet_time is not None:
                time_since_last = current_time - self.last_packet_time
                if time_since_last < self.delay:
                    return False  # Must wait for delay
            
            self.last_packet_time = current_time
            # Reset TTL timer when sending packet
            self.last_activity_time = current_time
        
        # Determine packet color based on value/type
        if value == "SYN":
            packet_color = QColor(255, 100, 100)  # Red for SYN
        elif value == "ACK":
            packet_color = QColor(100, 100, 255)  # Blue for ACK
        elif value == "SERVICE":
            packet_color = QColor(255, 165, 0)  # Orange for service discovery
        elif value == "CONNECTION_REQUEST":
            packet_color = QColor(255, 200, 0)  # Yellow for connection request
        elif value == "CONNECTION_RESPONSE":
            packet_color = QColor(200, 255, 0)  # Yellow-green for connection response
        else:
            packet_color = QColor(100, 200, 100)  # Green for data packets
        
        # Create and send packet
        packet = Packet(source_node, destination_id, value, packet_color, packet_data)
        self.packets.append(packet)
        
        # Store connection reference for when packet arrives
        packet.connection = self
        packet.target_node = target_node
        packet.source_node_obj = source_node
        
        return True