# -*- coding: utf-8 -*-
"""
Quantum Image Processing - Local Simulation
=============================================
Encodes a 2x2 classical image into a quantum state using the FRQI protocol,
applies QFT frequency analysis, a custom decoupling (eraser) sequence,
reconstructs the image, and runs it on a local simulator.

Based on: https://colab.research.google.com/drive/1invdBE63MisDMIYazsqAYcPaGYsiJvMZ
"""

# ──────────────────────────────────────────────
# Prerequisites (run once in your terminal):
#   pip install qiskit qiskit-aer matplotlib
# ──────────────────────────────────────────────

from qiskit import QuantumCircuit, ClassicalRegister
from qiskit.circuit.library import QFT
from qiskit_aer import AerSimulator
from qiskit import transpile
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
import numpy as np


# =============================================
# PHASE 1: FRQI Image Encoding
# =============================================
# 2 qubits for pixel positions (4 pixels: 00, 01, 10, 11)
# 1 qubit for color (theta angle)
# Total = 3 qubits

qc = QuantumCircuit(3)

# Create spatial superposition — spreads circuit across all 4 pixel locations
qc.h(0)
qc.h(1)

# Define our 2x2 classical image colors as rotation angles
theta_00 = np.pi / 2   # Pixel 00 (Top-left)    — Dark
theta_01 = 0.0          # Pixel 01 (Top-right)   — Light
theta_10 = 0.0          # Pixel 10 (Bottom-left)  — Light
theta_11 = np.pi / 2   # Pixel 11 (Bottom-right) — Dark

# Encode colors using Multi-Controlled Y-Rotations (mcry)

# Pixel 00
qc.x(0)
qc.x(1)
qc.mcry(2 * theta_00, [0, 1], 2)
qc.x(1)
qc.x(0)

# Pixel 01
qc.x(1)
qc.mcry(2 * theta_01, [0, 1], 2)
qc.x(1)

# Pixel 10
qc.x(0)
qc.mcry(2 * theta_10, [0, 1], 2)
qc.x(0)

# Pixel 11 (no X gates needed — already in state |11⟩)
qc.mcry(2 * theta_11, [0, 1], 2)

print("=" * 55)
print("  Phase 1: FRQI Image Encoding — Complete")
print("=" * 55)
print(qc.draw("text"))


# =============================================
# PHASE 2: QFT Sorting Machine
# =============================================
qc.barrier()

# 2-qubit QFT on the spatial qubits (0, 1). Color qubit (2) passes through.
qft_circuit = QFT(num_qubits=2, do_swaps=True, inverse=False, name="QFT")
qc.append(qft_circuit, [0, 1])
qc = qc.decompose("QFT")

print("\n" + "=" * 55)
print("  Phase 2: QFT Sorting Machine — Complete")
print("=" * 55)
print(qc.draw("text"))


# =============================================
# PHASE 3: Custom Eraser (Decoupling Sequence)
# =============================================
qc.barrier()

alpha = np.pi / 4  # Rotation angle to push state toward equator

# Ry rotation on high-frequency target (Qubit 1)
qc.ry(alpha, 1)

# Hadamard flips from X-axis to Z-axis
qc.h(1)

# CNOT decoupler — forces destructive interference on Qubit 1
qc.cx(0, 1)

print("\n" + "=" * 55)
print("  Phase 3: Custom Eraser Sequence — Complete")
print("=" * 55)
print(qc.draw("text"))


# =============================================
# PHASE 4: Reconstructor
# =============================================
qc.barrier()

# Inverse eraser (run the Phase 3 sequence in strict reverse)
qc.cx(0, 1)
qc.h(1)
qc.ry(-alpha, 1)

# Inverse QFT to convert frequencies back into spatial pixels
iqft_circuit = qft_circuit.inverse()
iqft_circuit.name = "IQFT"
qc.append(iqft_circuit, [0, 1])
qc = qc.decompose("IQFT")

# Add classical register & measure all 3 qubits
cr = ClassicalRegister(3, "c")
qc.add_register(cr)
qc.measure([0, 1, 2], [0, 1, 2])

print("\n" + "=" * 55)
print("  Phase 4: Reconstructor — Complete")
print("=" * 55)
print(qc.draw("text"))


# =============================================
# PHASE 5: Local Simulation
# =============================================
print("\n" + "=" * 55)
print("  Phase 5: Running Local Simulation")
print("=" * 55)

simulator = AerSimulator()
compiled_circuit = transpile(qc, simulator)

# Run 10 000 shots for accurate probability estimates
job = simulator.run(compiled_circuit, shots=10000)
result = job.result()
counts = result.get_counts(qc)

print("Measurement Results (Binary):", counts)

plot_histogram(counts, title="Reconstructed Quantum Image Data")
plt.tight_layout()
plt.show()
