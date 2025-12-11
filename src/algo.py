from collections import deque
import heapq


def build_graph_from_canvas(canvas):
    # Graph construction algorithm - Builds weighted graph from canvas connections for pathfinding
    # Time Complexity: O(E), Space Complexity: O(V + E)
    # V = number of vertices (nodes), E = number of edges (connections)
    graph = {}
    
    if not canvas or not hasattr(canvas, 'connections'):
        return graph
    
    for conn in canvas.connections:
        if conn.state not in [conn.HANDSHAKING, conn.ESTABLISHED, conn.ACTIVE]:
            continue
        
        node_a_enabled = getattr(conn.node_a, 'enabled', True)
        node_b_enabled = getattr(conn.node_b, 'enabled', True)
        if not node_a_enabled or not node_b_enabled:
            continue
        
        node_a_id = getattr(conn.node_a, 'id', None)
        node_b_id = getattr(conn.node_b, 'id', None)
        
        if not node_a_id or not node_b_id:
            continue
        
        delay = conn.delay if conn.delay > 0 else 1
        
        if node_a_id not in graph:
            graph[node_a_id] = []
        if node_b_id not in graph:
            graph[node_b_id] = []
        
        graph[node_a_id].append((node_b_id, delay))
        graph[node_b_id].append((node_a_id, delay))
    
    return graph


def dijkstra_shortest_path(graph, start_id, destination_id):
    # Dijkstra's algorithm - Finds shortest path between nodes considering connection delays (weights)
    # Time Complexity: O((V + E) log V), Space Complexity: O(V)
    # V = number of vertices (nodes), E = number of edges (connections)
    if start_id not in graph or destination_id not in graph:
        return None, None
    
    if start_id == destination_id:
        return [start_id], 0
    
    distances = {node_id: float('inf') for node_id in graph}
    distances[start_id] = 0
    
    previous = {node_id: None for node_id in graph}
    
    pq = [(0, start_id)]
    visited = set()
    
    while pq:
        current_dist, current_id = heapq.heappop(pq)
        
        if current_id in visited:
            continue
        
        visited.add(current_id)
        
        if current_id == destination_id:
            path = []
            node = destination_id
            while node is not None:
                path.append(node)
                node = previous[node]
            path.reverse()
            return path, current_dist
        
        for neighbor_id, edge_delay in graph.get(current_id, []):
            if neighbor_id in visited:
                continue
            
            new_dist = current_dist + edge_delay
            
            if new_dist < distances[neighbor_id]:
                distances[neighbor_id] = new_dist
                previous[neighbor_id] = current_id
                heapq.heappush(pq, (new_dist, neighbor_id))
    
    return None, None


def bfs_shortest_path(graph, start_id, destination_id):
    # BFS (Breadth-First Search) - Finds path with minimum number of hops between nodes
    # Time Complexity: O(V + E), Space Complexity: O(V)
    # V = number of vertices (nodes), E = number of edges (connections)
    if start_id not in graph or destination_id not in graph:
        return None, None
    
    if start_id == destination_id:
        return [start_id], 0
    
    queue = deque([(start_id, [start_id])])
    visited = {start_id}
    
    while queue:
        current_id, path = queue.popleft()
        
        for neighbor_id, _ in graph.get(current_id, []):
            if neighbor_id in visited:
                continue
            
            visited.add(neighbor_id)
            new_path = path + [neighbor_id]
            
            if neighbor_id == destination_id:
                return new_path, len(new_path) - 1
            
            queue.append((neighbor_id, new_path))
    
    return None, None


def find_path(canvas, start_id, destination_id, algorithm='dijkstra'):
    # Pathfinding wrapper - Selects and runs the specified pathfinding algorithm (dijkstra or bfs)
    # Time Complexity: O((V + E) log V) for dijkstra, O(V + E) for bfs
    # V = number of vertices (nodes), E = number of edges (connections)
    graph = build_graph_from_canvas(canvas)
    
    if not graph:
        return None, None
    
    if algorithm == 'dijkstra':
        return dijkstra_shortest_path(graph, start_id, destination_id)
    elif algorithm == 'bfs':
        return bfs_shortest_path(graph, start_id, destination_id)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}. Use 'dijkstra' or 'bfs'")


def initiate_path_discovery(start_node, target_service_id):
    # Packet-based path discovery - Sends discovery packets through network to find paths (legacy method)
    if not start_node.canvas_ref:
        return False
    
    if not hasattr(start_node, 'discovery_counter'):
        start_node.discovery_counter = 0
    start_node.discovery_counter += 1
    discovery_id = f"{start_node.id}_{target_service_id}_{start_node.discovery_counter}"
    
    discovery_data = {
        "target_service_id": target_service_id,
        "requesting_node_id": start_node.id,
        "path": [start_node.id],
        "total_delay": 0,
        "discovery_id": discovery_id
    }
    
    sent_count = 0
    for conn in start_node.canvas_ref.connections:
        if conn.state not in [conn.HANDSHAKING, conn.ESTABLISHED, conn.ACTIVE]:
            continue
        
        node_a_enabled = getattr(conn.node_a, 'enabled', True)
        node_b_enabled = getattr(conn.node_b, 'enabled', True)
        if not node_a_enabled or not node_b_enabled:
            continue
        
        neighbor_node = None
        if conn.node_a == start_node:
            neighbor_node = conn.node_b
        elif conn.node_b == start_node:
            neighbor_node = conn.node_a
        
        if neighbor_node and hasattr(neighbor_node, 'id'):
            if start_node.send_packet(neighbor_node.id, "PATH_DISCOVERY", discovery_data):
                sent_count += 1
                print(f"Path discovery: {start_node.id} -> {neighbor_node.id} (state: {conn.state})")
    
    print(f"Path discovery initiated from {start_node.id} to {target_service_id}: sent {sent_count} packets")
    return sent_count > 0
