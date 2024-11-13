import sympy as sym
from sympy import pprint

# Load the SPICE netlist from a file
def loadNetlist(filePath):
    with open(filePath, 'r') as f:
        return f.read().splitlines()

# Generate a new unique symbol with a prefix for circuit elements
def createSymbol(symbolList, prefix):
    count = sum(1 for s in symbolList if str(s).startswith(prefix))
    newSymbol = sym.Symbol(prefix + str(count + 1))
    symbolList.append(newSymbol)
    return newSymbol

# Parse the netlist to count nodes, currents, and voltage sources
def parseNetlist(netlist):
    nodes = set()  # Set to store all unique nodes
    currentSymbols = []  # List to store symbols for currents and inductors
    currentCount = 0
    voltageSourceCount = 0

    for line in netlist:
        parts = line.split()
        nodes.update(parts[1:3])  # Add nodes from each line
        element = parts[0]
        if element in ('L', 'D', 'S', 'E'):  # Elements that require additional equations
            currentSymbols.append(element)
            currentCount += 1
            if element == 'E':  # Count voltage sources separately
                voltageSourceCount += 1

    if '0' in nodes:  # Remove ground node from node count
        nodes.remove('0')

    return len(nodes), currentCount, voltageSourceCount, currentSymbols

# Initialize variables for node voltages and currents
def initializeVariables(nodeCount, currentSymbols):
    variables = sym.zeros(nodeCount + len(currentSymbols), 1)
    for i in range(nodeCount):
        variables[i] = sym.Symbol('V' + str(i))  # Node voltages
    for i, current in enumerate(currentSymbols):
        variables[nodeCount + i] = sym.Symbol('I' + current)  # Current symbols
    variableDerivatives = variables.diff("t")  # Time derivatives of variables
    return variables, variableDerivatives

# Add stamp for a resistor to the conductance matrix
def resistorStamp(nodeA, nodeB, conductanceMatrix, symbol):
    conductanceMatrix[nodeA, nodeA] += symbol
    conductanceMatrix[nodeA, nodeB] -= symbol
    conductanceMatrix[nodeB, nodeA] -= symbol
    conductanceMatrix[nodeB, nodeB] += symbol

# Add stamp for a capacitor to the capacitance matrix
def capacitorStamp(nodeA, nodeB, capacitanceMatrix, symbol):
    capacitanceMatrix[nodeA, nodeA] += symbol
    capacitanceMatrix[nodeA, nodeB] -= symbol
    capacitanceMatrix[nodeB, nodeA] -= symbol
    capacitanceMatrix[nodeB, nodeB] += symbol

# Add stamp for an inductor to the conductance and capacitance matrices
def inductorStamp(nodeA, nodeB, conductanceMatrix, capacitanceMatrix, symbol, index):
    conductanceMatrix[nodeA, index] += 1
    conductanceMatrix[nodeB, index] -= 1
    conductanceMatrix[index, nodeA] += 1
    conductanceMatrix[index, nodeB] -= 1
    capacitanceMatrix[index, index] -= symbol

# Add stamp for a voltage source to the conductance and RHV matrices
def voltageSourceStamp(nodeA, nodeB, conductanceMatrix, rhvMatrix, symbol, index):
    conductanceMatrix[nodeA, index] += 1
    conductanceMatrix[nodeB, index] -= 1
    conductanceMatrix[index, nodeA] += 1
    conductanceMatrix[index, nodeB] -= 1
    rhvMatrix[index] += symbol

# Build the MNA matrices based on the netlist
def buildMnaMatrices(netlist, nodeCount, currentSymbols):
    symbolList = []
    dimension = nodeCount + len(currentSymbols)
    conductanceMatrix = sym.zeros(dimension, dimension)
    capacitanceMatrix = sym.zeros(dimension, dimension)
    rhvMatrix = sym.zeros(dimension, 1)

    for line in netlist:
        parts = line.split()
        nodeA = int(parts[1]) - 1
        nodeB = int(parts[2]) - 1
        element = parts[0]
        symbol = None
        index = None

        if element == 'R':
            symbol = createSymbol(symbolList, 'G')
            resistorStamp(nodeA, nodeB, conductanceMatrix, symbol)
        elif element == 'L':
            symbol = createSymbol(symbolList, 'L')
            index = nodeCount + currentSymbols.index(element)
            inductorStamp(nodeA, nodeB, conductanceMatrix, capacitanceMatrix, symbol, index)
        elif element in ('S', 'D'):
            symbol = createSymbol(symbolList, 'p')
            index = nodeCount + currentSymbols.index(element)
            inductorStamp(nodeA, nodeB, conductanceMatrix, capacitanceMatrix, symbol, index)
        elif element == 'E':
            symbol = createSymbol(symbolList, 'E')
            index = nodeCount + currentSymbols.index(element)
            voltageSourceStamp(nodeA, nodeB, conductanceMatrix, rhvMatrix, symbol, index)
        elif element == 'C':
            symbol = createSymbol(symbolList, 'C')
            capacitorStamp(nodeA, nodeB, capacitanceMatrix, symbol)
        else:
            raise ValueError(f"Unknown element {element}")

    return conductanceMatrix, capacitanceMatrix, rhvMatrix


def displayResults(variables, variableDerivatives, conductanceMatrix, capacitanceMatrix, rhvMatrix):
    print("MNA Equation:")
    pprint(sym.Eq(conductanceMatrix * variables + capacitanceMatrix * variableDerivatives, rhvMatrix))


def main():
    netlistFilePath = "buck.txt"
    netlist = loadNetlist(netlistFilePath)
    nodeCount, currentCount, voltageSourceCount, currentSymbols = parseNetlist(netlist)
    variables, variableDerivatives = initializeVariables(nodeCount, currentSymbols)
    conductanceMatrix, capacitanceMatrix, rhvMatrix = buildMnaMatrices(netlist, nodeCount, currentSymbols)
    displayResults(variables, variableDerivatives, conductanceMatrix, capacitanceMatrix, rhvMatrix)


if __name__ == '__main__':
    main()
