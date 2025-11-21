from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QComboBox
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter

class ControlBar(QWidget):
    # Control bar widget with buttons for node management
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas_ref = None  # Reference to canvas
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Node type selector
        self.node_type_combo = QComboBox()
        self.node_type_combo.addItem("Normal Node", "normal")
        self.node_type_combo.addItem("Special Node", "special")
        self.node_type_combo.setStyleSheet("""
            QComboBox {
                padding: 5px 10px;
                font-size: 13px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
        """)
        layout.addWidget(self.node_type_combo)
        
        self.new_node_button = QPushButton("New Node")
        self.new_node_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 14px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.new_node_button.clicked.connect(self._on_new_node_clicked)
        layout.addWidget(self.new_node_button)
        
        # Add spacing to push buttons to the left
        layout.addStretch()
        
        self.setLayout(layout)
        self.setFixedHeight(50)
    
    def set_canvas(self, canvas):
        """Set the canvas reference"""
        self.canvas_ref = canvas
    
    def _on_new_node_clicked(self):
        """Handle new node button click"""
        if not self.canvas_ref:
            return
        
        # Get selected node type
        node_type = self.node_type_combo.currentData()
        
        # Generate a unique ID for the new node
        import random
        import string
        existing_ids = [node.id for node in self.canvas_ref.nodes if node.id]
        new_id = None
        while new_id is None or new_id in existing_ids:
            new_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Start positioning mode
        def on_position_saved(x, y):
            self.canvas_ref.add_node(x, y, node_type=node_type, id=new_id, url=None)
        
        def on_cancel():
            pass  # Just exit positioning mode
        
        self.canvas_ref.start_positioning(node_type, on_position_saved, on_cancel)
    
    def paintEvent(self, event):
        # Override to set background color
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(220, 220, 230))
