from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QComboBox, QLineEdit, QSpinBox
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import Qt, QTimer

class PacketSidebar(QWidget):
    #Left sidebar widget for packet sending controls
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_node = None
        self.canvas_ref = None
        self.continuous_timers = {}  # Track continuous sending timers by target node ID
        
        # Set up layout
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Title
        self.title_label = QLabel("Packet Controls")
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
        
        # Node info
        self.node_info_label = QLabel("No node selected")
        self.node_info_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #555;
                padding: 3px;
            }
        """)
        layout.addWidget(self.node_info_label)
        
        # Send Single Packet Section
        packet_separator = QFrame()
        packet_separator.setFrameShape(QFrame.HLine)
        packet_separator.setFrameShadow(QFrame.Sunken)
        packet_separator.setStyleSheet("color: #ccc; margin-top: 10px; margin-bottom: 10px;")
        layout.addWidget(packet_separator)
        
        packet_title = QLabel("Send Single Packet")
        packet_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding: 5px;
            }
        """)
        layout.addWidget(packet_title)
        
        # Target node selector
        target_label = QLabel("Target Node:")
        target_label.setStyleSheet("font-size: 13px; color: #555;")
        layout.addWidget(target_label)
        
        self.target_node_combo = QComboBox()
        self.target_node_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                font-size: 13px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
        """)
        layout.addWidget(self.target_node_combo)
        
        # Message input
        message_label = QLabel("Message (optional):")
        message_label.setStyleSheet("font-size: 13px; color: #555;")
        layout.addWidget(message_label)
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter message...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                font-size: 13px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
        """)
        layout.addWidget(self.message_input)
        
        # Send button
        self.send_packet_button = QPushButton("Send Packet")
        self.send_packet_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px;
                font-size: 13px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.send_packet_button.clicked.connect(self._on_send_packet)
        self.send_packet_button.setEnabled(False)
        layout.addWidget(self.send_packet_button)
        
        # Continuous Sending Section
        continuous_separator = QFrame()
        continuous_separator.setFrameShape(QFrame.HLine)
        continuous_separator.setFrameShadow(QFrame.Sunken)
        continuous_separator.setStyleSheet("color: #ccc; margin-top: 10px; margin-bottom: 10px;")
        layout.addWidget(continuous_separator)
        
        continuous_title = QLabel("Continuous Sending")
        continuous_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding: 5px;
            }
        """)
        layout.addWidget(continuous_title)
        
        # Target node selector for continuous
        continuous_target_label = QLabel("Target Node:")
        continuous_target_label.setStyleSheet("font-size: 13px; color: #555;")
        layout.addWidget(continuous_target_label)
        
        self.continuous_target_combo = QComboBox()
        self.continuous_target_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                font-size: 13px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
        """)
        layout.addWidget(self.continuous_target_combo)
        
        # Packets per second
        pps_label = QLabel("Packets per Second:")
        pps_label.setStyleSheet("font-size: 13px; color: #555;")
        layout.addWidget(pps_label)
        
        self.pps_spinbox = QSpinBox()
        self.pps_spinbox.setMinimum(1)
        self.pps_spinbox.setMaximum(100)
        self.pps_spinbox.setValue(10)
        self.pps_spinbox.setStyleSheet("""
            QSpinBox {
                padding: 8px;
                font-size: 13px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
        """)
        layout.addWidget(self.pps_spinbox)
        
        # Start/Stop continuous button
        self.continuous_button = QPushButton("Start Continuous")
        self.continuous_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                padding: 10px;
                font-size: 13px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
            QPushButton:pressed {
                background-color: #B71C1C;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.continuous_button.clicked.connect(self._on_toggle_continuous)
        self.continuous_button.setEnabled(False)
        layout.addWidget(self.continuous_button)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #666;
                padding: 5px;
                min-height: 20px;
            }
        """)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        self.setLayout(layout)
        self.setFixedWidth(250)
        self.hide()
        
        # Set background
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-right: 1px solid #ddd;
            }
        """)
    
    def set_selected_node(self, node, canvas_ref):
        #Update the sidebar to show information for the selected node
        self.selected_node = node
        self.canvas_ref = canvas_ref
        
        if node:
            self.node_info_label.setText(f"Node: {node.id or 'Unnamed'}")
            self._populate_target_nodes()
            self.send_packet_button.setEnabled(True)
            self.continuous_button.setEnabled(True)
            self.show()
        else:
            # Stop any continuous sending when node is deselected
            self._stop_all_continuous()
            self.node_info_label.setText("No node selected")
            self.send_packet_button.setEnabled(False)
            self.continuous_button.setEnabled(False)
            self.hide()
    
    def _populate_target_nodes(self):
        #Populate target node dropdowns with all nodes in the network
        self.target_node_combo.clear()
        self.continuous_target_combo.clear()
        
        if not self.canvas_ref or not hasattr(self.canvas_ref, 'nodes'):
            return
        
        # Get all nodes except the selected node
        all_nodes = []
        for node in self.canvas_ref.nodes:
            if hasattr(node, 'id') and node.id:
                # Skip the selected node itself
                if self.selected_node and node == self.selected_node:
                    continue
                all_nodes.append((node.id, node))
        
        if all_nodes:
            # Sort by node ID for easier selection
            all_nodes.sort(key=lambda x: x[0])
            for node_id, node in all_nodes:
                display_text = f"{node_id} ({node.node_type})"
                self.target_node_combo.addItem(display_text, node)
                self.continuous_target_combo.addItem(display_text, node)
        else:
            self.target_node_combo.addItem("No other nodes", None)
            self.continuous_target_combo.addItem("No other nodes", None)
    
    def _on_send_packet(self):
        #Handle send single packet button click
        if not self.selected_node:
            return
        
        target_node = self.target_node_combo.currentData()
        if not target_node:
            self.status_label.setText("No target node selected")
            return
        
        message = self.message_input.text().strip()
        
        # Create packet data with message
        packet_data = {"message": message} if message else None
        value = f"MSG: {message}" if message else "DATA"
        
        result = self.selected_node.send_packet(target_node.id, value, packet_data)
        if result:
            self.status_label.setText(f"Packet sent to {target_node.id}")
            self.message_input.clear()
        else:
            self.status_label.setText(f"Failed to send packet to {target_node.id}")
    
    def _on_toggle_continuous(self):
        #Handle start/stop continuous sending
        if not self.selected_node:
            return
        
        target_node = self.continuous_target_combo.currentData()
        if not target_node:
            self.status_label.setText("No target node selected")
            return
        
        target_id = target_node.id
        
        if target_id in self.continuous_timers:
            # Stop continuous sending
            self._stop_continuous(target_id)
            self.continuous_button.setText("Start Continuous")
            self.continuous_button.setStyleSheet("""
                QPushButton {
                    background-color: #F44336;
                    color: white;
                    border: none;
                    padding: 10px;
                    font-size: 13px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #D32F2F;
                }
                QPushButton:pressed {
                    background-color: #B71C1C;
                }
            """)
            self.status_label.setText(f"Stopped continuous sending to {target_id}")
        else:
            # Start continuous sending
            pps = self.pps_spinbox.value()
            interval_ms = 1000 / pps  # Convert packets per second to interval in milliseconds
            
            timer = QTimer()
            timer.timeout.connect(lambda: self._send_continuous_packet(target_node))
            timer.start(int(interval_ms))
            
            self.continuous_timers[target_id] = timer
            self.continuous_button.setText("Stop Continuous")
            self.continuous_button.setStyleSheet("""
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
            self.status_label.setText(f"Started continuous sending to {target_id} ({pps} pps)")
    
    def _send_continuous_packet(self, target_node):
        #Send a packet as part of continuous sending
        if not self.selected_node:
            return
        
        # Send packet with a counter or timestamp as message
        from PySide6.QtCore import QDateTime
        timestamp = QDateTime.currentMSecsSinceEpoch()
        packet_data = {"message": f"Continuous packet {timestamp}", "continuous": True}
        
        self.selected_node.send_packet(target_node.id, "DATA", packet_data)
    
    def _stop_continuous(self, target_id):
        #Stop continuous sending to a specific target
        if target_id in self.continuous_timers:
            timer = self.continuous_timers[target_id]
            timer.stop()
            timer.deleteLater()
            del self.continuous_timers[target_id]
    
    def _stop_all_continuous(self):
        #Stop all continuous sending
        for target_id in list(self.continuous_timers.keys()):
            self._stop_continuous(target_id)
    
    def paintEvent(self, event):
        #Override to ensure background is painted
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(245, 245, 245))
        super().paintEvent(event)

