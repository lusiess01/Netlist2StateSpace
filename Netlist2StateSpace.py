import csv
import sympy as sp

# Parameters for the state-space model initialization
Vi, R, L, C = sp.symbols('Vi R L C')  # Component values
i_L, v_C = sp.symbols('i_L v_C')      # State variables
switch_state = sp.symbols('switch_state')  # Switch state (1 = closed, 0 = open)

# Function to read the netlist from a CSV file
def read_netlist(filename):
    elements = []
    with open(filename, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            elements.append(row)
    return elements

# Function to process the netlist and generate the state-space model
def process_netlist(elements):
    # Example processing to recognize switch states and components
    for element in elements:
        element_type = element['Element']
        if element_type == 'E':
            Vi = sp.symbols(element['Value'])
        elif element_type == 'L':
            L = sp.symbols(element['Value'])
        elif element_type == 'R':
            R = sp.symbols(element['Value'])
        elif element_type == 'C':
            C = sp.symbols(element['Value'])
        elif element_type in ['D', 'S'] and element['Type'] == 'Ideal switch':
            switch_state = 1  # Assume the switch is closed

    # Define state differential equations
    di_L_dt = sp.Piecewise(
        ((Vi - v_C - R * i_L) / L, switch_state == 1),  # Closed switch
        (0, switch_state == 0)                          # Open switch
    )
    dv_C_dt = i_L / C

    # Define state vector and equations
    X = sp.Matrix([i_L, v_C])            # State vector
    X_dot = sp.Matrix([di_L_dt, dv_C_dt]) # State derivatives
    U = sp.Matrix([Vi])                   # Input vector (Vi as input voltage)
    Y = sp.Matrix([v_C])                  # Output vector (e.g., voltage across capacitor)

    # Determine state-space matrices (X_dot = A*X + B*U, Y = C*X + D*U)
    A = X_dot.jacobian(X)
    B = X_dot.jacobian(U)
    C_matrix = Y.jacobian(X)
    D_matrix = Y.jacobian(U)

    # Output the state-space matrices
    print("System matrix A:")
    sp.pprint(A)
    print("\nInput matrix B:")
    sp.pprint(B)
    print("\nOutput matrix C:")
    sp.pprint(C_matrix)
    print("\nDirect transmission matrix D:")
    sp.pprint(D_matrix)

# Example call
netlist = read_netlist("buck.csv")  # CSV filename
process_netlist(netlist)