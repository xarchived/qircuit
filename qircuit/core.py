import csv
from typing import Generator
from typing import List
from typing import Text

import numpy as np


class Qubit:
    index: int
    partition: int

    def __init__(self, index: int, partition: int):
        self.index = index
        self.partition = partition

    def __repr__(self):
        return f'<Qubit(index={self.index}, partition={self.partition})>'


class Gate:
    name: Text
    index: int
    qubits: List[Qubit]
    matrix: np.matrix

    def is_local(self) -> bool:
        # Make a set of all partition
        partitions = {qubit.partition for qubit in self.qubits}

        # Python set will ignore all duplicate values, so local gates have 1 partition
        if len(partitions) == 1:
            return True
        return False

    def is_global(self) -> bool:
        return not self.is_local()

    def is_single(self) -> bool:
        if len(self.qubits) > 1:
            return False
        return True

    def is_cnot(self) -> bool:
        if self.name == 'cnot':
            return True
        return False

    def is_diagonal(self) -> bool:
        i, j = np.nonzero(self.matrix)
        return np.all(i == j)

    def is_structured(self) -> bool:
        t = self.matrix
        if not t.shape == (2, 2):
            raise ValueError('Only single-qubit have structure')

        return (t[0, 0] == t[1, 1] and t[0, 1] == t[1, 0]) or (-t[0, 0] == t[1, 1] and -t[0, 1] == t[1, 0])

    def __init__(self, name: Text, matrix: np.matrix, *qubits: Qubit):
        self.name = name
        self.index = -1
        self.qubits = []
        self.matrix = matrix

        for qubit in qubits:
            self.qubits.append(qubit)

    def __repr__(self):
        clean_matrix = str(self.matrix).replace('\n', ",")
        return f'<Gate(name={self.name}, matrix={clean_matrix}, index={self.index + 1})>'


class Circuit:
    qubits: List[Qubit]
    gates: List[Gate]

    def add_qubit(self, index: int, partition: int) -> None:
        # Expand our list if its necessary
        delta = index - (len(self.qubits) - 1)
        if delta != 0:
            self.qubits += [None] * delta

        # If it's a new qubit we added to our list
        if self.qubits[index] is None:
            self.qubits[index] = Qubit(index, partition)

    def add_gate(self, gate: Gate) -> None:
        # First we add all qubits
        for qubit in gate.qubits:
            self.add_qubit(qubit.index, qubit.partition)

        # Calculate index and assign it to gate
        gate.index = len(self.gates)

        # Add gate to list
        self.gates.append(gate)

    @property
    def local_gates(self) -> List[Gate]:
        return [gate for gate in self.gates if gate.is_local()]

    @property
    def global_gates(self) -> List[Gate]:
        return [gate for gate in self.gates if gate.is_global()]

    def __init__(self, circuit_file: Text, gates_file: Text):
        self.qubits = [None]
        self.gates = []

        def get_csv_rows(path: Text) -> List:
            rows = []
            with open(path) as csv_file:
                csv_reader = csv.reader(csv_file, skipinitialspace=True)

                for row in csv_reader:
                    rows.append(row)

            return rows

        def get_qubits(row: List[Text]) -> Generator[None, Qubit, None]:
            for cell in row[1:]:  # First cell is gate name
                index, partition = [int(v) for v in cell.split('-')]
                yield Qubit(index, partition)

        def get_matrix(gate_name: Text) -> np.matrix:
            for matrix_row in get_csv_rows(gates_file):
                if gate_name == matrix_row[0]:
                    return np.matrix(matrix_row[1])

            raise ValueError(f'Gate "{gate_name}" not found in "{gates_file}"')

        for gate_row in get_csv_rows(circuit_file):  # Each line of file is a gate
            name = gate_row[0]  # First cell is gate name
            qubits = list(get_qubits(gate_row))
            matrix = get_matrix(name)
            new_gate = Gate(name, matrix, *qubits)
            self.add_gate(new_gate)

    def __str__(self):
        res = '\n'
        cur = 0

        def empty_row() -> Text:
            return f' {"¦   ¦" * len(self.gates)}\n'

        for idx, qubit in enumerate(self.qubits):
            if cur != qubit.partition:
                cur = qubit.partition
                res += empty_row()
                res += empty_row()

            res += empty_row()
            res += str(idx)
            for gate in self.gates:
                if gate.name == 'cnot':
                    if gate.qubits[0].index == idx:
                        res += "¦―•―¦"
                        continue
                    if gate.qubits[1].index == idx:
                        res += "¦―⊕―¦"
                        continue
                else:
                    if gate.qubits[0].index == idx:
                        res += "¦―□―¦"
                        continue

                res += "¦―――¦"
            res += '\n'

        res += empty_row()

        return res

    def __repr__(self):
        return f'<Circuit(qubits={len(self.qubits)}, gates={len(self.gates)})>'
