import csv
import sympy as sp


class MNACircuit:
    def __init__(self, netlist_file):
        self.netlist = []
        self.node_map = {}
        self.num_nodes = 0
        self.voltage_sources = []
        self.read_netlist(netlist_file)
        self.build_matrices()

    def read_netlist(self, netlist_file):
        with open(netlist_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) < 4:
                    continue  # Skip rows that don't have enough values
                element, node_i, node_j, value = row
                # Process the value as either a number or a symbol (if variable)
                if value == '':
                    value = None  # Empty value treated as ideal switch
                else:
                    try:
                        value = float(value)  # Try to convert to float
                    except ValueError:
                        value = sp.symbols(value)  # Treat as symbol if it's not a number

                # Map nodes to indices
                if node_i not in self.node_map:
                    self.node_map[node_i] = self.num_nodes
                    self.num_nodes += 1
                if node_j not in self.node_map:
                    self.node_map[node_j] = self.num_nodes
                    self.num_nodes += 1
                
                # Add to the netlist
                self.netlist.append((element, node_i, node_j, value))
    
    def build_matrices(self):
        # Initialize symbolic matrices
        self.G = sp.zeros(self.num_nodes, self.num_nodes)  # Conductance matrix
        self.B = sp.zeros(self.num_nodes + len(self.voltage_sources), 1)  # Voltage sources matrix

        # Count voltage sources to expand MNA matrix for them
        self.v_source_count = 0
        for element, _, _, _ in self.netlist:
            if element.startswith('V') or element.startswith('E'):
                self.v_source_count += 1

        # Full MNA matrix: It includes both nodes and voltage sources
        size = self.num_nodes + self.v_source_count
        self.MNA = sp.zeros(size, size)

        # Populate G and B matrices
        for element, node_i, node_j, value in self.netlist:
            node_i = self.node_map.get(node_i, None)
            node_j = self.node_map.get(node_j, None)
            
            if node_i is None or node_j is None:
                print(f"Warning: Skipping invalid node pair ({node_i}, {node_j}) for element {element}")
                continue
            
            if element.startswith('R'):
                self.add_resistor(node_i, node_j, value)
            elif element.startswith('I'):
                self.add_current_source(node_i, node_j, value)
            elif element.startswith('V') or element.startswith('E'):
                self.add_voltage_source(node_i, node_j, value)
            elif element == 'S':  # Switch handling
                self.add_switch(node_i, node_j, value)
            elif element == 'L':  # Inductor or special handling
                self.add_inductor(node_i, node_j, value)
            elif element == 'C':  # Capacitor or special handling
                self.add_capacitor(node_i, node_j, value)
            elif element == 'D':  # Diode or special handling
                self.add_diode(node_i, node_j, value)

        # Copy G to MNA and add voltage sources
        self.MNA[:self.num_nodes, :self.num_nodes] = self.G

    def add_resistor(self, node_i, node_j, value):
        conductance = 1 / value if value is not None else 0
        self.G[node_i, node_i] += conductance
        self.G[node_j, node_j] += conductance
        self.G[node_i, node_j] -= conductance
        self.G[node_j, node_i] -= conductance

    def add_current_source(self, node_i, node_j, value):
        if value is None:
            return  # Ideal switch, no effect on matrix
        self.B[node_i, 0] += value
        self.B[node_j, 0] -= value

    def add_voltage_source(self, node_i, node_j, value):
        # For now, assuming the voltage source equation is added
        # This needs to be implemented if needed
        pass

    def add_switch(self, node_i, node_j, value):
        if value is None:
            # Ideal switch: We assume it has no effect when open
            return
        else:
            # You can add logic here for non-ideal switches if necessary
            pass

    def add_inductor(self, node_i, node_j, value):
        # If we consider an inductor as a symbolic value or special matrix logic
        pass

    def add_capacitor(self, node_i, node_j, value):
        # If we consider a capacitor as a symbolic value or special matrix logic
        pass

    def add_diode(self, node_i, node_j, value):
        # If we consider a diode as a symbolic value or special matrix logic
        pass


if __name__ == "__main__":
    # Path to the CSV file
    netlist_file = 'test.csv'
    circuit = MNACircuit(netlist_file)
    
    # Print the MNA matrix
    print("MNA Matrix:")
    sp.pprint(circuit.MNA)
