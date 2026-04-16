# -*- coding: utf-8 -*-
"""
Quantum Image Processing - IBM Quantum Hardware
=================================================
Runs the FRQI-encoded quantum image circuit on a REAL IBM Quantum processor
using the modern SamplerV2 primitive.

Prerequisites:
  pip install qiskit qiskit-ibm-runtime

Setup:
  1. Get your API token from https://quantum.ibm.com
  2. Set it as an environment variable:
       Windows (PowerShell):  $env:IBM_QUANTUM_TOKEN = "your-token-here"
       Linux / macOS:         export IBM_QUANTUM_TOKEN="your-token-here"
  3. Run this script:  python quantum_ibm_hardware.py
"""

import os
import numpy as np

from qiskit import QuantumCircuit, ClassicalRegister
from qiskit.circuit.library import QFT
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler


# =============================================
# Helper: Build the full quantum circuit
# =============================================
def build_quantum_image_circuit():
    """Build the complete FRQI image encoding + processing circuit."""

    qc = QuantumCircuit(3)

    # --- Phase 1: FRQI Image Encoding ---
    qc.h(0)
    qc.h(1)

    theta_00 = np.pi / 2   # Pixel 00 — Dark
    theta_01 = 0.0          # Pixel 01 — Light
    theta_10 = 0.0          # Pixel 10 — Light
    theta_11 = np.pi / 2   # Pixel 11 — Dark

    # Pixel 00
    qc.x(0); qc.x(1)
    qc.mcry(2 * theta_00, [0, 1], 2)
    qc.x(1); qc.x(0)

    # Pixel 01
    qc.x(1)
    qc.mcry(2 * theta_01, [0, 1], 2)
    qc.x(1)

    # Pixel 10
    qc.x(0)
    qc.mcry(2 * theta_10, [0, 1], 2)
    qc.x(0)

    # Pixel 11
    qc.mcry(2 * theta_11, [0, 1], 2)

    # --- Phase 2: QFT ---
    qc.barrier()
    qft_circuit = QFT(num_qubits=2, do_swaps=True, inverse=False, name="QFT")
    qc.append(qft_circuit, [0, 1])
    qc = qc.decompose("QFT")

    # --- Phase 3: Custom Eraser ---
    qc.barrier()
    alpha = np.pi / 4
    qc.ry(alpha, 1)
    qc.h(1)
    qc.cx(0, 1)

    # --- Phase 4: Reconstructor ---
    qc.barrier()
    qc.cx(0, 1)
    qc.h(1)
    qc.ry(-alpha, 1)

    iqft_circuit = qft_circuit.inverse()
    iqft_circuit.name = "IQFT"
    qc.append(iqft_circuit, [0, 1])
    qc = qc.decompose("IQFT")

    cr = ClassicalRegister(3, "c")
    qc.add_register(cr)
    qc.measure([0, 1, 2], [0, 1, 2])

    return qc


# =============================================
# Main: Run on IBM Quantum Hardware
# =============================================
def main():
    # ── Step 1: Read API token from environment ──
    token = os.environ.get("IBM_QUANTUM_TOKEN")
    if not token:
        print("ERROR: IBM_QUANTUM_TOKEN environment variable is not set.")
        print("Set it with:  $env:IBM_QUANTUM_TOKEN = 'your-token-here'  (PowerShell)")
        return

    print("=" * 55)
    print("  Phase 6: Connecting to IBM Quantum Hardware")
    print("=" * 55)

    # ── Step 2: Authenticate ──
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=token,
    )

    # ── Step 3: Find the least-busy real backend ──
    print("Searching for the least busy REAL quantum computer...")
    backend = service.least_busy(
        operational=True,
        simulator=False,
        min_num_qubits=3,
    )
    print(f"Connected to: {backend.name}")

    # ── Step 4: Build & transpile the circuit ──
    qc = build_quantum_image_circuit()
    print(f"Transpiling circuit for {backend.name}...")
    pm = generate_preset_pass_manager(target=backend.target, optimization_level=1)
    isa_circuit = pm.run(qc)

    # ── Step 5: Submit using SamplerV2 ──
    print("Submitting job via SamplerV2 (you may wait in a queue)...")
    sampler = Sampler(mode=backend)
    job = sampler.run([isa_circuit], shots=1024)
    print(f"Job ID: {job.job_id()}")
    print("Waiting for results — check your IBM dashboard for queue status.")

    # ── Step 6: Retrieve & display results ──
    real_result = job.result()
    real_counts = real_result[0].data.c.get_counts()

    print("\n" + "=" * 55)
    print("  REAL HARDWARE RESULTS")
    print("=" * 55)
    print("Measurement Results (Binary):", real_counts)


if __name__ == "__main__":
    main()
