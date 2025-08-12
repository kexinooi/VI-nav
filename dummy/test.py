import json
import networkx as nx
import matplotlib.pyplot as plt

# --- Load your JSON file ---
with open("hallway_graph.json") as f:
    data = json.load(f)

# --- Create the graph ---
G = nx.Graph()

# Add nodes with coordinates
for node, coords in data["nodes"].items():
    G.add_node(node, pos=tuple(coords))

# Add edges with weights
for edge in data["edges"]:
    G.add_edge(edge["from"], edge["to"], weight=edge["weight"])

# --- Ask user for start and end nodes ---
source = input("Enter start node: ").strip()
target = input("Enter end node: ").strip()

if source not in G.nodes or target not in G.nodes:
    print("❌ One of the nodes does not exist in the graph!")
else:
    # Shortest path calculation
    path = nx.shortest_path(G, source=source, target=target, weight="weight")
    distance = nx.shortest_path_length(G, source=source, target=target, weight="weight")

    print(f"\nShortest path from {source} to {target}: {path}")
    print(f"Total distance: {distance:.2f} units\n")

    # --- Plot the graph ---
    pos = nx.get_node_attributes(G, 'pos')

    # Draw all nodes and edges
    nx.draw(G, pos, with_labels=True, node_color="lightblue", node_size=500)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, 'weight'))

    # Highlight shortest path edges in red
    path_edges = list(zip(path, path[1:]))
    nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color="red", width=2)

    # Highlight path nodes in yellow
    nx.draw_networkx_nodes(G, pos, nodelist=path, node_color="yellow", node_size=600)

    plt.show()
