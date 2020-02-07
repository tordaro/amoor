import math
import pandas as pd
from util import rotate, cartesian

class Config:

    def __init__(self, config_path):
        config = pd.read_excel(config_path, sheet_name=["Ramme", "Anker"])
        self.frame_config = config["Ramme"]
        self.anchor_config = config["Anker"]
        # Encapsulate input values
        self.num_rows = int(self.frame_config.iloc[0, 1])
        self.num_cols = int(self.frame_config.iloc[1, 1])
        self.length_long = self.frame_config.iloc[2, 1]
        self.length_across = self.frame_config.iloc[3, 1]
        self.frame_depth = self.frame_config.iloc[4, 1]
        self.course = self.frame_config.iloc[5, 1] - 90  # 90 is drawing angle
        # Control variables 
        self.num_cages = self.num_rows * self.num_cols
        self.num_nodes = (self.num_rows + 1) * (self.num_cols + 1)
        self.num_lines = (
            (self.num_rows + 1) * self.num_cols
            + (self.num_cols + 1) * self.num_rows
        )
        # Unique IDs
        self.node_id = 1
        self.edge_id = 1
        # Make dictionaries
        self.nodes = {}  # Contains pos, id and dof
        self.edges = {}  # Contains edge and edge_id
        self.add_node_edges()

    def add_node_edges(self):
        self.make_frame_nodes()
        self.make_frame_egdes()
        self.make_hane_edges()
        self.make_slings_edges()
        self.make_anchor_lines()

    def make_anchor_lines(self):
        categories = ["_Toppkjetting", "_Tau", "_Bunnkjetting"]
        for row in self.anchor_config.iterrows():
            anchor_num = row[1][0]
            corner_num = row[1][1]
            horizontal_length = float(row[1][2])
            bottom_length = float(row[1][6])
            top_length = float(row[1][7])
            degree = float(row[1][3])
            depth = float(row[1][4])
            rel_depth = depth - self.frame_depth
            tot_length = (horizontal_length**2 + rel_depth**2) ** 0.5
            mid_length = tot_length - bottom_length 
            # Set nodes 
            cos_elv = horizontal_length / tot_length # cos(elevation angle)
            lengths = [top_length, mid_length, tot_length]
            node_names = [corner_num]
            for length in lengths:
                node_name = round(
                    anchor_num + (tot_length - length) / 1e3, 3
                )
                node_names.append(node_name)
                x, y = cartesian(
                    length * cos_elv,
                    degree,
                    self.nodes[corner_num]["pos"][0],
                    self.nodes[corner_num]["pos"][1]
                )
                z = -length * rel_depth / tot_length - self.frame_depth
                self.nodes[node_name] = {
                    "pos": (x, y, z),
                    "id": self.node_id,
                    "dof": (length != tot_length)
                }
                self.node_id += 1
            # Set edges
            for i, category in enumerate(categories):
                self.edges[str(anchor_num)+category]= {
                    "edge": (node_names[i], node_names[i+1]),
                    "edge_id": self.edge_id + i * len(self.anchor_config)
                }
            self.edge_id += 1
        self.edge_id += len(self.anchor_config) * (len(categories) - 1)

    def make_frame_nodes(self):
        allowed_x = [i*self.length_long for i in range(self.num_cols+1)]
        allowed_y = [i*self.length_across for i in range(self.num_rows+1)]
        name = 301
        for x in allowed_x:
            for y in allowed_y:
                x_rot, y_rot = rotate(x, y, self.course)
                self.nodes[name] = {
                    "pos": (x_rot, y_rot, -self.frame_depth),
                    "id": self.node_id,
                    "dof": True
                }
                name += 1
                self.node_id += 1

    def make_hane_edges(self):
        if self.num_rows > 2:
            num_cages = self.num_cages - self.num_cols
        else:
            num_cages = self.num_cages
        for i in range(num_cages):
            self.edges[chr(65+i)+"_Hanefot"] = {"edge_id": self.edge_id}
            self.edge_id += 1
        
    def make_slings_edges(self):
        if self.num_rows > 2:
            num_cages = self.num_cages - self.num_cols
        else:
            num_cages = self.num_cages
        for i in range(num_cages):
            self.edges[chr(65+i)+"_Slings"] = {"edge_id": self.edge_id}
            self.edge_id += 1

    def make_frame_egdes(self):
        nodes_per_col = self.num_rows + 1 
        nodes_per_row = self.num_cols + 1
        # Make vertical lines
        name = 701
        node = 301
        for _ in range(nodes_per_row):
            for _ in range(self.num_rows):
                self.edges[str(name)+"_Ramme"] = {
                    "edge": (node, node+1),
                    "edge_id": self.edge_id
                }
                name += 1
                node += 1
                self.edge_id += 1
            name += nodes_per_col
            node += 1
        # Make horizontal lines
        name = 701 + self.num_rows
        node = 301
        for _ in range(self.num_cols):
            for _ in range(nodes_per_col):
                self.edges[str(name)+"_Ramme"] = {
                    "edge": (node, node+nodes_per_col),
                    "edge_id": self.edge_id
                }
                name += 1
                node += 1
                self.edge_id += 1
            name += self.num_rows
