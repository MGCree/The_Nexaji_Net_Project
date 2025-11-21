from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt
import math

class Packet:
    """Represents a data packet traveling between nodes"""
    
    def __init__(self, source_node, destination_id, value="", color=QColor(255, 100, 100), packet_data=None):
        self.source_node = source_node
        self.destination_id = destination_id
        self.value = value
        self.color = color
        self.packet_data = packet_data  # Additional data (for service discovery, etc.)
        self.progress = 0.0  # 0.0 to 1.0, how far along the path
        self.speed = 0.02  # Progress increment per frame
        self.active = True
        
    def update(self):
        """Update packet position"""
        if self.active:
            self.progress += self.speed
            if self.progress >= 1.0:
                self.active = False
                return True  # Packet reached destination
        return False
    
    def draw(self, painter: QPainter, target_x, target_y):
        """Draw the packet as a capsule shape along the path"""
        if not self.active:
            return
        
        # Calculate current position along the line
        source_x = self.source_node.x
        source_y = self.source_node.y
        
        current_x = source_x + (target_x - source_x) * self.progress
        current_y = source_y + (target_y - source_y) * self.progress
        
        # Draw capsule (rounded rectangle)
        capsule_width = 30
        capsule_height = 15
        radius = capsule_height / 2
        
        painter.save()
        painter.setPen(QPen(self.color, 2))
        painter.setBrush(self.color)
        
        # Draw capsule shape
        x = int(current_x - capsule_width / 2)
        y = int(current_y - capsule_height / 2)
        
        # Draw rounded rectangle (capsule)
        painter.drawRoundedRect(x, y, capsule_width, capsule_height, radius, radius)
        
        # Draw value text if provided
        if self.value:
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(x + 5, y + 12, self.value)
        
        painter.restore()

