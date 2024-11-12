import csv
import sympy as sp

class MNACircuit:
    def __init__(self, filename):
        self.netlist = []
        self.nodes = set()
        self.voltage_sources = []
        
        # Read the CSV file and parse components
        with open(filename, 'r') as file:
            reader = csv.reader(file, delimiter=',')  # Using comma delimiter
            for row in reader:
                # Skip rows that don't have exactly 4 elements or contain empty values
                if len(row) != 4 or any(val.strip() == '' for val in row):
                    continue
                
                element, node_i, node_j, value = row
                
                # Check if the value is an empty string (ideal switch)
                if value == '':  # Ideal switch
                    value = sp.symbols('Switch')  # Symbolic representation for the switch
                    # Alternatively, you could treat 'Switch' as zero or infinite resistance.
                    # For example, if you want to model a closed switch (perfect conductor):
                    # value = 0
                elif value.isalpha():  # Check if the value is a variable (alphabetic)
                    value = sp.symbols(value)  # Create a symbolic variable using sympy
                else:
                    try:
                        value = float(value)  # Try to convert to float
                    except ValueError:
                        value = sp.symbols(value)  # If it's not a valid number, treat as a symbol
                
                self.netlist.append((element, int(node_i), int(node_j), value))
                self.nodes.update([int(node_i), int(node_j)])
        
        self.nodes.discard(0)  # remove ground node
        self.num_nodes = len(self.nodes)
        self.node_map = {node: idx + 1 for idx, node in enumerate(self.nodes)}  # map nodes to indices
        self.node_map[0] = 0  # ground node at index 0
        self.build_matrices()

    def build_matrices(self):
        # Use sympy to create symbolic matrices
        self.G = sp.zeros(self.num_nodes, self.num_nodes)
        self.B = sp.zeros(self.num_nodes + len(self.voltage_sources), 1)
        self.v_source_count = 0

        # Count voltage sources to expand MNA matrix for them
        for element, _, _, _ in self.netlist:
            if element.startswith('V'):
                self.v_source_count += 1

        # Full MNA matrix
        size = self.num_nodes + self.v_source_count
        self.MNA = sp.zeros(size, size)

        # Populate G and B matrices
        for element, node_i, node_j, value in self.netlist:
            node_i = self.node_map[node_i]
            node_j = self.node_map[node_j]
            
            if element.startswith('R'):
                self.add_resistor(node_i, node_j, value)
            elif element.startswith('I'):
                self.add_current_source(node_i, node_j, value)
            elif element.startswith('V'):
                self.add_voltage_source(node_i, node_j, value)

        # Copy G to MNA and add voltage sources
        self.MNA[:self.num_nodes, :self.num_nodes] = self.G

    def add_resistor(self, node_i, node_j, resistance):
        if resistance == 0:  # Closed switch (ideal conductor)
            conductance = sp.oo  # Infinite conductance (perfect conductor)
        elif resistance == sp.oo:  # Open switch (ideal insulator)
            conductance = 0  # No conductance (perfect insulator)
        elif isinstance(resistance, sp.Basic):  # If the resistance is symbolic
            conductance = 1 / resistance
        else:
            conductance = 1 / resistance

        if node_i > 0:
            self.G[node_i - 1, node_i - 1] += conductance
        if node_j > 0:
            self.G[node_j - 1, node_j - 1] += conductance
        if node_i > 0 and node_j > 0:
            self.G[node_i - 1, node_j - 1] -= conductance
            self.G[node_j - 1, node_i - 1] -= conductance

    def add_current_source(self, node_i, node_j, current):
        if isinstance(current, sp.Basic):  # If the current is symbolic
            pass  # You can add symbolic handling here if needed
        if node_i > 0:
            self.B[node_i - 1] -= current
        if node_j > 0:
            self.B[node_j - 1] += current

    def add_voltage_source(self, node_i, node_j, voltage):
        v_idx = self.num_nodes + len(self.voltage_sources)
        self.voltage_sources.append((node_i, node_j, voltage))

        if node_i > 0:
            self.MNA[node_i - 1, v_idx] = 1
            self.MNA[v_idx, node_i - 1] = 1
        if node_j > 0:
            self.MNA[node_j - 1, v_idx] = -1
            self.MNA[v_idx, node_j - 1] = -1

        self.B[v_idx] = voltage

    def solve(self):
        # Solve the symbolic MNA matrix
        solution = sp.linsolve((self.MNA, self.B))
        print("Solution (Node Voltages and Source Currents):\n", solution)

# Example usage
circuit = MNACircuit('test.csv')
circuit.solve()
