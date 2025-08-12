import json
import networkx as nx
import matplotlib.pyplot as plt

# Load JSON
with open("hallway_graph.json") as f:
    data = json.load(f)

# Create graph
G = nx.Graph()

# Add nodes with coordinates
for node, coords in data["nodes"].items():
    G.add_node(node, pos=tuple(coords))

# Add edges with weights
for edge in data["edges"]:
    G.add_edge(edge["from"], edge["to"], weight=edge["weight"])

# Print nodes to verify
print("Nodes in graph:", list(G.nodes))

# Example shortest path from A to H
path = nx.shortest_path(G, source="A", target="H", weight="weight")
print("Shortest path A → H:", path)

# Draw graph
pos = nx.get_node_attributes(G, 'pos')
nx.draw(G, pos, with_labels=True, node_color="lightblue", node_size=500)
labels = nx.get_edge_attributes(G, 'weight')
nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
plt.show()
