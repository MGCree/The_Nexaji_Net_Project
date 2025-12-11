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
        self.enabled = True  # Node is enabled by default (can send/receive packets)
        self.pending_path_discoveries = {}  # Track pending path discoveries: discovery_id -> {"callback": func, "best_path": path, "best_delay": delay}
        self.seen_discovery_ids = set()  # Track seen discovery IDs to prevent loops
        self.discovery_counter = 0  # Counter for unique discovery IDs

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

        # Load existing data if file exists
        if os.path.exists(self.file_path):
            self._load_from_json()
        else:
            self._save_to_json()
        
        # Initialize services file if it doesn't exist
        if not os.path.exists(self.services_file_path):
            self._save_services_to_json()
    
    def _load_from_json(self):
        #Load node data from JSON file
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
                # Update node properties from saved data
                if "neighbours" in data:
                    self.neighbours = data["neighbours"]
                if "url" in data:
                    self.url = data["url"]
                if "x" in data:
                    self.x = data["x"]
                if "y" in data:
                    self.y = data["y"]
                if "enabled" in data:
                    self.enabled = data["enabled"]
        except Exception as e:
            print(f"Error loading node data from {self.file_path}: {e}")

    def _save_to_json(self):
        data = {
            "id": self.id,
            "type": self.node_type,
            "x": self.x,
            "y": self.y,
            "url": self.url,
            "neighbours": self.neighbours,
            "enabled": self.enabled,
        }
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=4)
    
    def _save_services_to_json(self):
        #Save discovered services to the second JSON file
        if not hasattr(self, 'discovered_services'):
            self.discovered_services = []
        
        with open(self.services_file_path, "w") as f:
            json.dump(self.discovered_services, f, indent=4)
    
    def _load_services_from_json(self):
        #Load discovered services from the second JSON file
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
        #Check if the services.json file is empty or has no services
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
        If no direct connection exists, finds a path and routes through it.
        Returns True if packet was sent, False otherwise.
        packet_data: Optional dictionary with additional packet information (for service discovery)
        """
        # Check if node is enabled
        if not self.enabled:
            return False
        
        if not self.canvas_ref or not hasattr(self.canvas_ref, 'connections'):
            return False
        
        # First, try direct connection (fast path)
        target_connection = None
        for conn in self.canvas_ref.connections:
            # Check if this connection involves current node and the destination
            other_node = None
            if conn.node_a == self:
                if hasattr(conn.node_b, 'id') and conn.node_b.id == destination_id:
                    other_node = conn.node_b
            elif conn.node_b == self:
                if hasattr(conn.node_a, 'id') and conn.node_a.id == destination_id:
                    other_node = conn.node_a
            
            if other_node:
                target_connection = conn
                break
        
        if target_connection:
            # Direct connection exists, use it
            result = target_connection.send_packet(self, destination_id, value, packet_data)
            if not result and value == "CONNECTION_REQUEST" and packet_data:
                self._send_connection_failure(packet_data, destination_id)
            return result
        
        # No direct connection - find a path and route through it
        path = self._find_path_to_node(destination_id)
        if not path or len(path) < 2:
            # No path found
            if value == "CONNECTION_REQUEST" and packet_data:
                self._send_connection_failure(packet_data, destination_id)
            return False
        
        # Route packet through the path
        # Send to first node in path (next hop)
        next_node_id = path[1]
        # Add routing information to packet data
        if packet_data is None:
            packet_data = {}
        packet_data = packet_data.copy()
        packet_data["routing_path"] = path
        packet_data["final_destination"] = destination_id
        packet_data["source_node"] = self.id
        
        # Send to next hop
        for conn in self.canvas_ref.connections:
            other_node = None
            if conn.node_a == self:
                if hasattr(conn.node_b, 'id') and conn.node_b.id == next_node_id:
                    other_node = conn.node_b
            elif conn.node_b == self:
                if hasattr(conn.node_a, 'id') and conn.node_a.id == next_node_id:
                    other_node = conn.node_a
            
            if other_node:
                return conn.send_packet(self, next_node_id, value, packet_data)
        
        return False
    
    def _find_path_to_node(self, destination_id):
        """
        Find a path from this node to the destination using Dijkstra's algorithm.
        Uses the graph-based pathfinding from algo.py which considers connection delays.
        Returns a list of node IDs representing the path, or None if no path exists.
        
        Time Complexity: O((V + E) log V) where V is vertices, E is edges
        """
        if not self.canvas_ref:
            return None
        
        from algo import find_path
        
        # Use Dijkstra's algorithm to find shortest path considering delays
        path, total_delay = find_path(self.canvas_ref, self.id, destination_id, algorithm='dijkstra')
        
        return path
    
    def _forward_routed_packet(self, packet_data, value):
        """Forward a routed packet to the next hop in the path"""
        routing_path = packet_data.get("routing_path", [])
        final_destination = packet_data.get("final_destination")
        if not routing_path or not final_destination or len(routing_path) < 2:
            return False
        
        # Find our position in the path
        try:
            our_index = routing_path.index(self.id)
            if our_index + 1 >= len(routing_path):
                # We're the last node, should have been delivered
                return False
            
            next_node_id = routing_path[our_index + 1]
            
            # Forward to next node
            return self.send_packet(next_node_id, value, packet_data)
        except ValueError:
            # We're not in the path
            return False
    
    def _send_connection_failure(self, original_request_data, failed_at_node_id):
        """Send a connection failure packet back to the requesting node"""
        requesting_node_id = original_request_data.get("requesting_node_id")
        if not requesting_node_id:
            return
        
        # IMPORTANT: Only the requesting node should handle failures and initiate path discovery
        # Intermediate nodes should only forward failure packets back
        
        # If we're the requesting node, handle the failure directly
        if requesting_node_id == self.id:
            self._handle_connection_failure(original_request_data, failed_at_node_id)
            return
        
        # Otherwise, we're an intermediate node - just forward the failure packet back
        path = original_request_data.get("path", [])
        if not path or self.id not in path:
            return
        
        try:
            our_index = path.index(self.id)
            if our_index > 0:
                prev_node_id = path[our_index - 1]
                failure_data = {
                    "original_request": original_request_data,
                    "failed_at_node_id": failed_at_node_id,
                    "requesting_node_id": requesting_node_id,
                    "path": path[:our_index + 1]  # Path from requesting node to failure point
                }
                # Just forward - don't handle it ourselves
                self.send_packet(prev_node_id, "CONNECTION_FAILURE", failure_data)
        except ValueError:
            pass
    
    def _handle_connection_failure(self, original_request_data, failed_at_node_id):
        """Handle a connection failure at the requesting node"""
        # Check retry count
        retry_count = original_request_data.get("retry_count", 0)
        service_id = original_request_data.get("service_id")
        
        if not service_id:
            print("Connection failure: No service_id in request data")
            return
        
        if retry_count == 0:
            # First failure - retry once with same path
            print(f"Connection request failed at {failed_at_node_id}, retrying...")
            # Create retry data with incremented retry count
            retry_data = original_request_data.copy()
            retry_data["retry_count"] = 1
            # Retry the connection request with same path
            next_node_id = retry_data.get("path", [])
            if len(next_node_id) > 1:
                next_node_id = next_node_id[1]
                result = self.send_packet(next_node_id, "CONNECTION_REQUEST", retry_data)
                if not result:
                    # Retry also failed, trigger pathfinding
                    self._handle_connection_failure(retry_data, next_node_id)
        else:
            # Second failure - use packet-based pathfinding
            # IMPORTANT: Only the requesting node should reach here
            requesting_node_id = original_request_data.get("requesting_node_id")
            if requesting_node_id != self.id:
                print(f"ERROR: Intermediate node {self.id} tried to initiate path discovery! This should not happen.")
                return
            
            print(f"Connection request failed again at {failed_at_node_id}, initiating path discovery...")
            if self.canvas_ref:
                from algo import initiate_path_discovery
                
                # Store callback to use the discovered path
                if not hasattr(self, 'discovery_counter'):
                    self.discovery_counter = 0
                self.discovery_counter += 1
                discovery_id = f"{self.id}_{service_id}_{self.discovery_counter}"
                
                def on_path_discovered(path, total_delay):
                    """Callback when path is discovered"""
                    if path and len(path) > 1:
                        print(f"Found new path via discovery: {path} (delay: {total_delay}ms)")
                        
                        # Update services.json with the new path
                        if hasattr(self, 'discovered_services'):
                            # Find the service entry and update it
                            service_updated = False
                            for service in self.discovered_services:
                                if service.get("service_id") == service_id:
                                    # Update with new path (reverse it for storage - path goes from service to node)
                                    service["path"] = list(reversed(path))
                                    service["total_delay"] = total_delay
                                    service_updated = True
                                    print(f"Updated service {service_id} with new path in services.json")
                                    break
                            
                            if not service_updated:
                                # Service not in discovered_services, add it
                                # We need to get service info - try to find it from the path
                                target_node = None
                                if self.canvas_ref:
                                    for node in self.canvas_ref.nodes:
                                        if hasattr(node, 'id') and node.id == service_id:
                                            target_node = node
                                            break
                                
                                if target_node:
                                    new_service = {
                                        "service_id": service_id,
                                        "service_url": getattr(target_node, 'url', None),
                                        "service_type": "Unknown",  # We don't know the type from path discovery
                                        "path": list(reversed(path)),  # Reverse for storage
                                        "total_delay": total_delay
                                    }
                                    self.discovered_services.append(new_service)
                                    print(f"Added service {service_id} to discovered_services")
                            
                            # Save to JSON
                            self._save_services_to_json()
                        
                        # Create new request with new path
                        new_request_data = {
                            "service_id": service_id,
                            "requesting_node_id": self.id,
                            "path": path,
                            "request_type": "CONNECTION_REQUEST",
                            "retry_count": 0  # Reset retry count for new path
                        }
                        # Send request to first node in new path
                        next_node_id = path[1] if len(path) > 1 else None
                        if next_node_id:
                            result = self.send_packet(next_node_id, "CONNECTION_REQUEST", new_request_data)
                            if not result:
                                print(f"Failed to send connection request on new path to {next_node_id}")
                            else:
                                print(f"Retrying connection request with new path: {path}")
                        else:
                            print("New path is invalid (no next node)")
                    else:
                        print(f"No path found to service {service_id}")
                
                # Store callback with initial state
                self.pending_path_discoveries[discovery_id] = {
                    "callback": on_path_discovered,
                    "best_path": None,
                    "best_delay": float('inf'),
                    "timeout": None,
                    "callback_called": False  # Track if we've already called the callback
                }
                
                # Set timeout to use best path found so far (wait longer for responses to traverse network)
                from PySide6.QtCore import QTimer
                def use_best_path():
                    if discovery_id in self.pending_path_discoveries:
                        info = self.pending_path_discoveries[discovery_id]
                        if info["best_path"]:
                            print(f"Path discovery timeout - using best path found: {info['best_path']} (delay: {info['best_delay']}ms)")
                            if not info.get("callback_called", False):
                                info["callback"](info["best_path"], info["best_delay"])
                        else:
                            print(f"Path discovery timeout - no path found to service {service_id}")
                        del self.pending_path_discoveries[discovery_id]
                
                timer = QTimer()
                timer.setSingleShot(True)
                timer.timeout.connect(use_best_path)
                timer.start(10000)  # 10 second timeout (increased to allow time for responses to traverse network)
                self.pending_path_discoveries[discovery_id]["timeout"] = timer
                
                # Initiate path discovery
                if not initiate_path_discovery(self, service_id):
                    print("Failed to initiate path discovery")
                    # Clean up
                    if discovery_id in self.pending_path_discoveries:
                        del self.pending_path_discoveries[discovery_id]
    
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
        # Check if node is enabled
        if not self.enabled:
            return
        
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
    
    def request_service_connection(self, service_data, retry_data=None):
        """
        Request a connection to a service by following the path from services.json.
        Sends a CONNECTION_REQUEST packet along the path.
        The path in services.json goes FROM service TO this node, so we need to reverse it.
        
        Args:
            service_data: Service data from discovered_services
            retry_data: Optional retry data from a previous failed attempt
        """
        if not self.canvas_ref:
            return False
        
        # If retry_data is provided, use it (for retries)
        if retry_data:
            path = retry_data.get("path", [])
            service_id = retry_data.get("service_id")
        else:
            # Path in services.json is from service to this node, reverse it for request
            original_path = service_data.get("path", [])
            if len(original_path) == 0:
                return False
            
            # Reverse the path to go from this node to the service
            path = list(reversed(original_path))
            service_id = service_data.get("service_id")
        
        # Verify we're at the start of the path
        if path[0] != self.id:
            # We're not at the start, find our position
            try:
                our_index = path.index(self.id)
                # Trim path to start from us
                path = path[our_index:]
            except ValueError:
                # We're not in the path, can't route
                return False
        
        # Get the next node in the path (towards the service)
        if len(path) < 2:
            # We're the service itself or path is invalid
            return False
        
        next_node_id = path[1]
        
        # Create connection request packet with the path
        request_data = {
            "service_id": service_id,
            "requesting_node_id": self.id,
            "path": path,  # Path from requesting node to service
            "request_type": "CONNECTION_REQUEST",
            "retry_count": retry_data.get("retry_count", 0) if retry_data else 0
        }
        
        # Send request packet to next node in path
        result = self.send_packet(next_node_id, "CONNECTION_REQUEST", request_data)
        if not result:
            print(f"Failed to send connection request from {self.id} to {next_node_id}. Path: {path}")
        return result
    
    def handle_connection_request(self, request_data, sender_node):
        """
        Handle a connection request packet.
        If we're the service, respond with CONNECTION_RESPONSE.
        Otherwise, forward along the path.
        """
        # Check if node is enabled
        if not self.enabled:
            # Send failure packet back
            self._send_connection_failure(request_data, self.id)
            return False
        
        service_id = request_data.get("service_id")
        path = request_data.get("path", [])
        requesting_node_id = request_data.get("requesting_node_id")
        
        # Check if we're the target service
        if self.id == service_id:
            # We're the service! Send response back
            response_data = {
                "service_id": service_id,
                "requesting_node_id": requesting_node_id,
                "path": list(reversed(path)),  # Reverse path for response
                "request_type": "CONNECTION_RESPONSE"
            }
            
            # Send response back along reversed path
            if len(path) > 1:
                # Find previous node in path
                our_index = path.index(self.id)
                if our_index > 0:
                    prev_node_id = path[our_index - 1]
                    return self.send_packet(prev_node_id, "CONNECTION_RESPONSE", response_data)
            return False
        else:
            # Forward along the path
            try:
                our_index = path.index(self.id)
                if our_index + 1 < len(path):
                    next_node_id = path[our_index + 1]
                    result = self.send_packet(next_node_id, "CONNECTION_REQUEST", request_data)
                    if not result:
                        # Forwarding failed - the failure is at the next node (we can't reach it)
                        # Send failure packet back to requesting node
                        self._send_connection_failure(request_data, next_node_id)
                    return result
            except ValueError:
                pass
            # Can't forward - we're the failure point
            self._send_connection_failure(request_data, self.id)
            return False
    
    def handle_path_discovery(self, discovery_data, sender_node, connection_delay):
        """
        Handle a PATH_DISCOVERY packet.
        If we're the target service, send PATH_RESPONSE back.
        Otherwise, forward to all neighbors (avoiding loops).
        """
        # Check if node is enabled
        if not self.enabled:
            return False
        
        discovery_id = discovery_data.get("discovery_id")
        target_service_id = discovery_data.get("target_service_id")
        requesting_node_id = discovery_data.get("requesting_node_id")
        path_so_far = discovery_data.get("path", [])
        total_delay = discovery_data.get("total_delay", 0)
        
        # Check if we've seen this discovery ID before (prevent loops)
        if discovery_id in self.seen_discovery_ids:
            return False  # Already processed this discovery
        
        # Add ourselves to seen discoveries
        self.seen_discovery_ids.add(discovery_id)
        
        # Clean up old discovery IDs periodically (keep set from growing too large)
        if len(self.seen_discovery_ids) > 1000:
            # Keep only recent ones (simple cleanup)
            self.seen_discovery_ids = set(list(self.seen_discovery_ids)[-500:])
        
        # Check if we're the target service
        if self.id == target_service_id:
            # We're the target! Send response back along the path
            complete_path = path_so_far + [self.id]
            print(f"Path discovery SUCCESS: Found path from {requesting_node_id} to {target_service_id}: {complete_path} (delay: {total_delay}ms)")
            response_data = {
                "target_service_id": target_service_id,
                "requesting_node_id": requesting_node_id,
                "path": complete_path,  # Complete path
                "total_delay": total_delay,
                "discovery_id": discovery_id
            }
            
            # Send response back to previous node in path
            if len(path_so_far) > 0:
                prev_node_id = path_so_far[-1]
                return self.send_packet(prev_node_id, "PATH_RESPONSE", response_data)
            return False
        else:
            # Forward to all neighbors (except the one we came from)
            sent_count = 0
            new_path = path_so_far + [self.id]
            
            for conn in self.canvas_ref.connections:
                # Allow path discovery through HANDSHAKING, ESTABLISHED, and ACTIVE connections
                # This allows discovery to find paths even through connections that aren't fully established
                if conn.state not in [conn.HANDSHAKING, conn.ESTABLISHED, conn.ACTIVE]:
                    continue
                
                # Check if both nodes are enabled
                node_a_enabled = getattr(conn.node_a, 'enabled', True)
                node_b_enabled = getattr(conn.node_b, 'enabled', True)
                if not node_a_enabled or not node_b_enabled:
                    continue
                
                # Find the neighbor node
                neighbor_node = None
                if conn.node_a == self:
                    neighbor_node = conn.node_b
                elif conn.node_b == self:
                    neighbor_node = conn.node_a
                
                # Don't send back to sender or if already in path (avoid loops)
                if neighbor_node and hasattr(neighbor_node, 'id'):
                    neighbor_id = neighbor_node.id
                    sender_id = getattr(sender_node, 'id', None)
                    if neighbor_id != sender_id and neighbor_id not in new_path:
                        # Create new discovery data with updated path
                        new_discovery_data = discovery_data.copy()
                        new_discovery_data["path"] = new_path
                        # Use connection delay, or estimate based on distance if delay is 0
                        conn_delay = conn.delay if conn.delay > 0 else 1
                        new_discovery_data["total_delay"] = total_delay + conn_delay
                        
                        if self.send_packet(neighbor_id, "PATH_DISCOVERY", new_discovery_data):
                            sent_count += 1
            
            return sent_count > 0
    
    def handle_path_response(self, response_data, sender_node):
        """
        Handle a PATH_RESPONSE packet.
        If we're the requesting node, store the best path and call callback when timeout.
        Otherwise, forward back along the path.
        """
        # Check if node is enabled
        if not self.enabled:
            return False
        
        requesting_node_id = response_data.get("requesting_node_id")
        discovery_id = response_data.get("discovery_id")
        path = response_data.get("path", [])
        total_delay = response_data.get("total_delay", float('inf'))
        
        # Check if we're the requesting node
        if self.id == requesting_node_id:
            # We're the requester! Store the best path found so far
            if discovery_id in self.pending_path_discoveries:
                info = self.pending_path_discoveries[discovery_id]
                # Check if this is a better path
                was_first_path = (info["best_delay"] == float('inf'))
                is_better_path = (total_delay < info["best_delay"])
                
                if is_better_path:
                    # Update best path
                    info["best_path"] = path
                    info["best_delay"] = total_delay
                    print(f"Received path response: {path} (delay: {total_delay}ms)")
                    
                    # If this is the first path found OR a better path, use it immediately
                    if not info.get("callback_called", False):
                        # Cancel the original timeout
                        if info.get("timeout"):
                            info["timeout"].stop()
                        
                        # Call the callback immediately with this path
                        if was_first_path:
                            print(f"Using first path found immediately: {path}")
                        else:
                            print(f"Using better path found: {path}")
                        info["callback"](path, total_delay)
                        info["callback_called"] = True
                        
                        # Don't delete yet - keep it in case we get a better path
                        # But set a shorter timeout for additional paths (3 seconds)
                        from PySide6.QtCore import QTimer
                        def use_best_path_final():
                            if discovery_id in self.pending_path_discoveries:
                                del self.pending_path_discoveries[discovery_id]
                        
                        timer = QTimer()
                        timer.setSingleShot(True)
                        timer.timeout.connect(use_best_path_final)
                        timer.start(3000)  # 3 second timeout for additional better paths
                        info["timeout"] = timer
            else:
                # Discovery entry was cleaned up (timeout fired), but we still got a response
                # This can happen if the response arrives just after timeout
                # Try to find the service and use the path anyway
                print(f"Path response arrived after timeout, but using path anyway: {path}")
                # Extract service_id from discovery_id (format: requesting_node_id_service_id_counter)
                parts = discovery_id.split('_')
                if len(parts) >= 2:
                    service_id = '_'.join(parts[1:-1])  # Everything between first and last part
                    # Try to use the path by creating a connection request
                    new_request_data = {
                        "service_id": service_id,
                        "requesting_node_id": self.id,
                        "path": path,
                        "request_type": "CONNECTION_REQUEST",
                        "retry_count": 0
                    }
                    next_node_id = path[1] if len(path) > 1 else None
                    if next_node_id:
                        result = self.send_packet(next_node_id, "CONNECTION_REQUEST", new_request_data)
                        if result:
                            print(f"Successfully sent connection request on late-arriving path")
            return True
        else:
            # Forward back along the path
            if len(path) > 1:
                try:
                    our_index = path.index(self.id)
                    if our_index > 0:
                        prev_node_id = path[our_index - 1]
                        return self.send_packet(prev_node_id, "PATH_RESPONSE", response_data)
                except ValueError:
                    pass
            return False
    
    def handle_connection_response(self, response_data, sender_node):
        """
        Handle a connection response packet.
        If we're the requesting node, the connection is now active.
        Otherwise, forward back along the path.
        Path in response goes from service to requesting node.
        """
        # Check if node is enabled
        if not self.enabled:
            return False
        requesting_node_id = response_data.get("requesting_node_id")
        path = response_data.get("path", [])
        
        # Check if we're the requesting node
        if self.id == requesting_node_id:
            # We're the requester! Connection is established and active
            # Mark all connections along the path as service connections
            if self.canvas_ref and hasattr(self.canvas_ref, 'connections'):
                # Mark all connections in the path as service connections
                # Path goes from service to requester
                for i in range(len(path) - 1):
                    current_node_id = path[i]
                    next_node_id = path[i + 1]
                    
                    # Find the connection between these nodes
                    for conn in self.canvas_ref.connections:
                        node_a_id = conn.node_a.id if hasattr(conn.node_a, 'id') else None
                        node_b_id = conn.node_b.id if hasattr(conn.node_b, 'id') else None
                        
                        if ((node_a_id == current_node_id and node_b_id == next_node_id) or
                            (node_a_id == next_node_id and node_b_id == current_node_id)):
                            # Mark as service connection and reset TTL
                            conn.is_service_connection = True
                            from PySide6.QtCore import QDateTime
                            conn.last_activity_time = QDateTime.currentMSecsSinceEpoch()
                            break
            return True
        else:
            # Forward back along the path (towards the requesting node)
            try:
                our_index = path.index(self.id)
                if our_index + 1 < len(path):
                    next_node_id = path[our_index + 1]  # Next node towards requester
                    return self.send_packet(next_node_id, "CONNECTION_RESPONSE", response_data)
            except ValueError:
                # We're not in the path, can't forward
                pass
            return False

    def send_signal(self, signal_range_pixels=150):
        """
        Send a connection signal that expands in a circle.
        signal_range_pixels: The radius in pixels (scaled from 30 meters)
        """
        # Check if node is enabled
        if not self.enabled:
            return
        
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
        # Check if node is enabled
        if not self.enabled:
            return
        
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
    def toggle_enabled(self):
        """Toggle the enabled state of the node"""
        self.enabled = not self.enabled
        self._save_to_json()  # Save the state
        return self.enabled

class NormalNode(Node):
    def __init__(self, x, y, id=None, url=None):
        super().__init__(x, y, id, url)
        self.node_type = "normal"
        # Only save if this is a new node (file didn't exist)
        if not os.path.exists(self.file_path):
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
        # Only save if this is a new node (file didn't exist)
        if not os.path.exists(self.file_path):
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
