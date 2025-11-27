from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QComboBox
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import Qt

class NodeSidebar(QWidget):
    """Sidebar widget that displays information and controls for the selected node"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_node = None
        self.canvas_ref = None
        
        # Set up layout
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Title
        self.title_label = QLabel("Node Information")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333;
                padding: 5px;
            }
        """)
        layout.addWidget(self.title_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #ccc;")
        layout.addWidget(separator)
        
        # Node info labels
        self.id_label = QLabel("ID: -")
        self.type_label = QLabel("Type: -")
        self.url_label = QLabel("URL: -")
        self.position_label = QLabel("Position: -")
        self.connections_label = QLabel("Connections: -")
        
        for label in [self.id_label, self.type_label, self.url_label, 
                      self.position_label, self.connections_label]:
            label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #555;
                    padding: 3px;
                }
            """)
            layout.addWidget(label)
        
        # Status panel
        status_separator = QFrame()
        status_separator.setFrameShape(QFrame.HLine)
        status_separator.setFrameShadow(QFrame.Sunken)
        status_separator.setStyleSheet("color: #ccc; margin-top: 10px; margin-bottom: 10px;")
        layout.addWidget(status_separator)
        
        status_title = QLabel("Current Status")
        status_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding: 5px;
            }
        """)
        layout.addWidget(status_title)
        
        self.status_label = QLabel("Idle")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #2196F3;
                padding: 8px;
                background-color: #E3F2FD;
                border-radius: 5px;
                min-height: 30px;
            }
        """)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Add spacing
        layout.addStretch()
        
        # Service discovery section (only for special nodes)
        self.service_separator = QFrame()
        self.service_separator.setFrameShape(QFrame.HLine)
        self.service_separator.setFrameShadow(QFrame.Sunken)
        self.service_separator.setStyleSheet("color: #ccc; margin-top: 10px; margin-bottom: 10px;")
        layout.addWidget(self.service_separator)
        
        self.service_title = QLabel("Service Discovery")
        self.service_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding: 5px;
            }
        """)
        layout.addWidget(self.service_title)
        
        self.service_type_combo = QComboBox()
        self.service_type_combo.addItems([
            "Web Server",
            "Database",
            "API Server",
            "File Server",
            "DNS Server",
            "Mail Server",
            "Game Server",
            "Streaming Server"
        ])
        self.service_type_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                font-size: 13px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
        """)
        layout.addWidget(self.service_type_combo)
        
        self.announce_service_button = QPushButton("Announce Service")
        self.announce_service_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 10px;
                font-size: 13px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
        """)
        self.announce_service_button.clicked.connect(self._on_announce_service)
        self.announce_service_button.setEnabled(False)
        layout.addWidget(self.announce_service_button)
        
        # Hide service section by default (only shown for special nodes)
        self.service_separator.setVisible(False)
        self.service_title.setVisible(False)
        self.service_type_combo.setVisible(False)
        self.announce_service_button.setVisible(False)
        
        # Connection request section (only for normal nodes)
        self.connection_separator = QFrame()
        self.connection_separator.setFrameShape(QFrame.HLine)
        self.connection_separator.setFrameShadow(QFrame.Sunken)
        self.connection_separator.setStyleSheet("color: #ccc; margin-top: 10px; margin-bottom: 10px;")
        layout.addWidget(self.connection_separator)
        
        self.connection_title = QLabel("Connect to Service")
        self.connection_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding: 5px;
            }
        """)
        layout.addWidget(self.connection_title)
        
        self.service_selector_combo = QComboBox()
        self.service_selector_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                font-size: 13px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
        """)
        layout.addWidget(self.service_selector_combo)
        
        self.connect_service_button = QPushButton("Connect")
        self.connect_service_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 13px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #2E7D32;
            }
        """)
        self.connect_service_button.clicked.connect(self._on_connect_service)
        self.connect_service_button.setEnabled(False)
        layout.addWidget(self.connect_service_button)
        
        # Hide connection section by default (only shown for normal nodes)
        self.connection_separator.setVisible(False)
        self.connection_title.setVisible(False)
        self.service_selector_combo.setVisible(False)
        self.connect_service_button.setVisible(False)
        
        # Buttons
        self.send_signal_button = QPushButton("Send Connection Signal")
        self.send_signal_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.send_signal_button.clicked.connect(self._on_send_signal)
        self.send_signal_button.setEnabled(False)
        layout.addWidget(self.send_signal_button)
        
        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                padding: 10px;
                font-size: 13px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        self.close_button.clicked.connect(self._on_close)
        layout.addWidget(self.close_button)
        
        self.setLayout(layout)
        self.setFixedWidth(250)
        self.hide()
        
        # Set background
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-left: 1px solid #ddd;
            }
        """)
    
    def set_selected_node(self, node, canvas_ref):
        """Update the sidebar to show information for the selected node"""
        self.selected_node = node
        self.canvas_ref = canvas_ref
        
        if node:
            self.id_label.setText(f"ID: {node.id or 'Unnamed'}")
            self.type_label.setText(f"Type: {node.node_type}")
            self.url_label.setText(f"URL: {node.url or 'None'}")
            self.position_label.setText(f"Position: ({int(node.x)}, {int(node.y)})")
            
            # Count connections
            connection_count = 0
            if canvas_ref and hasattr(canvas_ref, 'connections'):
                for conn in canvas_ref.connections:
                    if conn.node_a == node or conn.node_b == node:
                        connection_count += 1
            self.connections_label.setText(f"Connections: {connection_count}")
            
            # Update status
            self._update_status(node, canvas_ref)
            
            # Show/hide service discovery section based on node type
            is_special = node.node_type == "special"
            self.service_type_combo.setVisible(is_special)
            self.announce_service_button.setVisible(is_special)
            self.announce_service_button.setEnabled(is_special)
            self.service_title.setVisible(is_special)
            self.service_separator.setVisible(is_special)
            
            # Show/hide connection section based on node type (normal nodes)
            is_normal = node.node_type == "normal"
            self.connection_separator.setVisible(is_normal)
            self.connection_title.setVisible(is_normal)
            self.service_selector_combo.setVisible(is_normal)
            self.connect_service_button.setVisible(is_normal)
            
            # Populate service selector for normal nodes
            if is_normal:
                self._populate_service_selector(node)
            
            self.send_signal_button.setEnabled(True)
            self.show()
        else:
            self.hide()
    
    def _update_status(self, node, canvas_ref):
        """Update the status panel based on node's current activity"""
        if not node or not canvas_ref:
            self.status_label.setText("Idle")
            return
        
        status_parts = []
        
        # Check if node is sending a signal
        if hasattr(canvas_ref, 'active_signals'):
            for signal_ring in canvas_ref.active_signals:
                if hasattr(signal_ring, 'sender_node') and signal_ring.sender_node == node:
                    status_parts.append("Sending connection signal...")
                    break
        
        # Check connections and their states
        if hasattr(canvas_ref, 'connections'):
            handshake_count = 0
            established_count = 0
            active_count = 0
            packet_count = 0
            
            for conn in canvas_ref.connections:
                if conn.node_a == node or conn.node_b == node:
                    if conn.state == "handshaking":
                        handshake_count += 1
                        packet_count += len(conn.packets)
                    elif conn.state == "established":
                        established_count += 1
                    elif conn.state == "active":
                        active_count += 1
                        packet_count += len(conn.packets)
            
            if handshake_count > 0:
                status_parts.append(f"Handshaking with {handshake_count} node(s)")
            if established_count > 0:
                status_parts.append(f"Connection established with {established_count} node(s)")
            if active_count > 0:
                status_parts.append(f"Active connection(s): {active_count}")
            if packet_count > 0:
                status_parts.append(f"Transmitting {packet_count} packet(s)")
        
        if status_parts:
            self.status_label.setText("\n".join(status_parts))
        else:
            self.status_label.setText("Idle - Ready")
    
    def update_status(self):
        """Public method to update status (called from canvas)"""
        if self.selected_node and self.canvas_ref:
            self._update_status(self.selected_node, self.canvas_ref)
    
    def _on_send_signal(self):
        """Handle send signal button click"""
        if self.selected_node and self.canvas_ref:
            self.selected_node.send_signal(self.canvas_ref.signal_range_pixels)
    
    def _on_announce_service(self):
        """Handle announce service button click"""
        if self.selected_node and self.canvas_ref:
            service_type = self.service_type_combo.currentText()
            self.selected_node.send_service_discovery(service_type)
    
    def _populate_service_selector(self, node):
        """Populate the service selector dropdown with available services"""
        self.service_selector_combo.clear()
        
        if not hasattr(node, 'discovered_services'):
            node._load_services_from_json()
        
        if len(node.discovered_services) == 0:
            self.service_selector_combo.addItem("No services available")
            self.connect_service_button.setEnabled(False)
        else:
            for service in node.discovered_services:
                service_id = service.get("service_id", "Unknown")
                service_type = service.get("service_type", "Unknown")
                display_text = f"{service_id} ({service_type})"
                self.service_selector_combo.addItem(display_text, service)
            self.connect_service_button.setEnabled(True)
    
    def _on_connect_service(self):
        """Handle connect to service button click"""
        if self.selected_node and self.canvas_ref:
            current_index = self.service_selector_combo.currentIndex()
            if current_index >= 0:
                service_data = self.service_selector_combo.itemData(current_index)
                if service_data:
                    self.selected_node.request_service_connection(service_data)
    
    def _on_close(self):
        """Close the sidebar and deselect node"""
        if self.canvas_ref:
            self.canvas_ref.selected_node = None
            self.canvas_ref.update()
        self.set_selected_node(None, None)
    
    def paintEvent(self, event):
        """Override to ensure background is painted"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(245, 245, 245))
        super().paintEvent(event)

