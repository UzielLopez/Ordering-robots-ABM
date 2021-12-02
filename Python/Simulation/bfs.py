from .node import Node

# Find the closest box using bfs
def find_closest_box(start_position, m, n, boxes_positions):
    
    # If there is no boxes left, return a clue to the robot so it can stop moving
    if len(boxes_positions) == 0:
        return (-1, -1)

    current_node = Node(start_position)
    queue = []
    queue.append(current_node)
    while len(queue) != 0:

        current_node = queue[0]
        if current_node.position in boxes_positions:
            return current_node.position
        queue.pop(0)
        for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])
            # Make sure we are inbounds
            if node_position[0] > m - 1 or node_position[0] < 0 or node_position[1] > n - 1 or node_position[1] < 0:
                continue
            new_node = Node(node_position)
            queue.append(new_node)
