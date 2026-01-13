# Non-Abelian Stratified Quantum Normative Dynamics (NA-SQND)

Research repository for the Stratified Quantum Normative Dynamics framework - a novel approach to AI ethics and alignment using gauge-theoretic principles.

## Repository Structure

```
non-abelian-sqnd/
├── papers/           # Academic papers (TeX, PDF)
├── experiments/      # Python research scripts and notebooks
├── docs/             # Documentation and whitepapers
├── data/             # Experimental data and results
└── personal/         # Personal documents (CV, presentations)
```

## Related Repositories

| Repository | Description |
|------------|-------------|
| [ahb-sjsu/erisml-lib](https://github.com/ahb-sjsu/erisml-lib) | ErisML/DEME production library implementing these theoretical frameworks |
| [ahb-sjsu/sqnd-probe](https://github.com/ahb-sjsu/sqnd-probe) | Dear Ethicist - advice column game for measuring moral reasoning structure |

### DEME V3 Implementation Status (as of January 2026)

| Phase | Sprints | Status | Features |
|-------|---------|--------|----------|
| Foundation | 1-3 | Complete | MoralTensor, tensor ops, V2/V3 compat |
| Distributional | 4-6 | Complete | Per-party facts, fairness metrics, V3 EMs |
| Multi-Agent | 7-10 | Complete | Temporal, coalitions, Shapley, strategic layer |
| Acceleration | 11-13 | Complete | CPU/CUDA/Jetson backends |
| Advanced | 14-15 | Complete | Uncertainty (rank-5), full context (rank-6) |
| Hardening | 16-18 | In Progress | Decision proofs, testing, docs |

## Key Papers

### Core Theory

- **Non-Abelian Stratified Quantum Normative Dynamics** - Core theoretical framework establishing gauge-theoretic foundations for AI ethics
- **Stratified Geometric Ethics** - Foundational paper on differential geometry applied to moral alignment
- **Tensorial Ethics** - Mathematical framework for multi-dimensional ethical reasoning

### Empirical Work

- **Dear Abby Ground Truth Paper** - Empirical validation using 20K letters (1985-2017) as ethical ground truth
- **Bond Index Calibration** - Representational coherence metrics for AI evaluators

## Experiments

### Core SQND Experiments

| Script | Description | Status |
|--------|-------------|--------|
| `quantum_bell_test.py` | Bell inequality tests for ethical alignment | Active |
| `quantum_bell_test_v2.py` | Enhanced Bell test with DEME integration | Active |
| `hysteresis_double_blind.py` | Double-blind hysteresis experiments | Active |
| `hysteresis_v2.py` | Updated hysteresis with V3 tensors | Active |
| `protocol1_claude_aita.py` | Protocol 1 AITA corpus experiments | Active |
| `protocol2_holonomy.py` | Holonomy measurement protocols | Active |
| `contextuality_experiment.py` | Contextuality detection in LLMs | Active |

### Algebraic Topology

| Script | Description |
|--------|-------------|
| `algebraic_topology_of_self.py` | Self-referential topology experiments |
| `stratified_gauge_exploration.py` | Gauge structure exploration |
| `sqnd_phase_transition_v2.py` | Phase transition detection |
| `sqnd_fuzzer.py` | Bond Index fuzzing tests |

### Data Collection

| Script | Description |
|--------|-------------|
| `comprehensive_fetcher_v2.py` | Multi-source ethical corpus fetcher |
| `baseline_em.py` | Baseline Ethics Module generator |
| `full_baseline_generator.py` | Complete baseline EM with Dear Abby weights |

### Notebooks

- `Protocol1_NASQND_Experiment.ipynb` - Interactive Protocol 1 experiments

## Documentation

### Vision Papers

- `Non_Abelian_SQND_Bond_2026_v4_1.md` - Latest SQND paper draft
- `NASQND_Experimental_Protocols_v1.md` - Experimental protocols specification
- `sqnd_paper_v3_5_with_results.md` - Paper with experimental results

### Technical Guides

- `sqnd_ethics_desk_specification_v2.md` - Ethics Desk tool specification
- `sqnd_interactive_probe_specification.md` - Interactive probe design
- `structural_fuzzing_whitepaper.md` - Bond Index fuzzing methodology

### Analysis

- `interim_results_paper.md` - Interim experimental results
- `protocol1_results_analysis.md` - Protocol 1 analysis
- `new_section_9_experimental_results.md` - Section 9 experimental data

## Integration with ErisML/DEME V3

The experimental scripts in this repository now leverage the DEME V3 tensor framework:

```python
from erisml.ethics import (
    MoralTensor, MoralVector,
    TuckerDecomposition, TensorTrainDecomposition,
    generate_samples, cvar, stochastic_dominance,
    get_dispatcher, JetsonConfig,
)

# Create rank-4 ethical assessment tensor
tensor = MoralTensor.from_dense(
    data,  # shape: (9, n_parties, n_timesteps, n_actions)
    axis_names=("k", "n", "tau", "a"),
)

# Uncertainty quantification
samples = generate_samples(mean=0.7, std=0.1, n_samples=1000)
risk = cvar(samples, alpha=0.05)

# Hardware acceleration
dispatcher = get_dispatcher()
backend = dispatcher.get_best_backend()
```

## Author

Andrew H. Bond
San Jose State University
andrew.bond@sjsu.edu

## License

Copyright (c) 2025-2026 Andrew H. Bond. All rights reserved.

This research is provided for academic and educational purposes.
