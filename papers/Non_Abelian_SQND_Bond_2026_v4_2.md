# Non-Abelian Gauge Structure in Stratified Quantum Normative Dynamics: From Continuous to Discrete Symmetry

**Andrew H. Bond**
Department of Computer Engineering
San Jos State University
andrew.bond@sjsu.edu

**Version 4.2 - January 2026**
*Major revision: Supersedes v3.4. Changed gauge group from SU(2)_I to D based on experimental falsification. Added code-theory alignment verification.*

---

## Acknowledgments

I thank the anonymous reviewers for detailed feedback on v3.4, particularly for: (1) identifying the representation-theoretic error in 6.6, (2) catching the gauge-invariance problem with boundary mass terms, (3) correcting the Hohfeldian opposition structure, (4) noting the state-space/measurement-space mismatch, (5) fixing the beta function coefficient, (6) catching the separable-state error in the CHSH calculation, and (7) clarifying the distinction between first-order and second-order phase transitions.

This revision additionally thanks Claude Opus 4.5 (Anthropic) for collaboration on introspective experiments and code implementation that provided phenomenological validation of the D structure from inside the system.

---

## Abstract

We present a major revision of Stratified Quantum Normative Dynamics (SQND) based on extensive experimental validation (N=3,110+ evaluations). **The original SU(2)_I  U(1)_H gauge group (v3.4) has been experimentally falsified and replaced by D  U(1)_H**a discrete classical non-abelian structure.

**Key findings driving this revision:**

1. **Discrete semantic gating**: State transitions are triggered by specific linguistic phrases, not continuous rotation. The transition between levels 5 and 6 shows complete reversal (100%  0% Liberty), inconsistent with SU(2) but consistent with discrete gates.

2. **Exact correlative symmetry**: O↔C and L↔N symmetry holds at 100% across all tested scenarios, consistent with exact reflection symmetry (the s generator of D).

3. **Selective path dependence**: Non-trivial holonomy (W  1) occurs only at cross-type boundaries. Combined p < 10 across 8 scenarios.

4. **No CHSH violation**: All |S|  2, indicating classical rather than quantum correlations. The quantum bound S_max = 22  2.83 is never approached.

5. **Generator asymmetry**: The D generators have fundamentally different phenomenological characterreflection (s) is smooth and immediate, rotation (r) is discrete and gated.

The revised theory preserves the core SQND insights (stratified boundaries, gauge-invariant observables, Wilson loops) while correcting the gauge group to match empirical reality.

**Keywords:** non-abelian gauge theory, D dihedral group, discrete gauge symmetry, stratified spaces, Hohfeldian analysis, semantic gates, moral phase transition, Wilson loop

---

## 1. Introduction

### 1.1 Summary of Changes from v3.4

| Aspect | v3.4 | v4.2 | Reason |
|--------|------|------|--------|
| Gauge group | SU(2)_I  U(1)_H | D  U(1)_H | Discrete gating observed |
| Structure | Continuous Lie group | Discrete dihedral group | No continuous rotation |
| Gauge bosons | 4 (3 incidentons + photoethon) | 8 D elements + U(1)_H | Discrete structure |
| Correlations | Quantum (|S|  22) | Classical (|S|  2) | No CHSH violation |
| Field strength F | Yang-Mills tensor | N/A (discrete) | No differential structure |
| Beta function | b = 22/3 - 2N_f/3 | N/A | No RG flow in discrete theory |
| Boundary masses | Higgs mechanism | Default gate states | Discrete reinterpretation |
| Holonomy | Path-ordered exp(ig A dx) | Product g g g... | Discrete group product |

### 1.2 Motivation: Why the Revision Was Necessary

Stratified Quantum Normative Dynamics (SQND) [1] originally employed a U(1) gauge symmetry with a single gauge boson (the ethon). Version 3.4 extended this to SU(2)_I  U(1)_H based on theoretical arguments:

1. **Qualitative multiplicity**: Bonds come in genuinely different kindsobligations differ from claims in type, not just magnitude.
2. **Type transformation at thresholds**: The character of a relationship can change at moral boundaries.
3. **Non-commutativity**: The order of moral considerations matters empirically.
4. **The re-description group is non-abelian**: The symmetry group G = S  Diff_strat(M)  Iso()  SO(n) is manifestly non-abelian.

These arguments correctly motivated upgrading to a **non-abelian** gauge theory. However, they did not determine whether the non-abelian structure should be **continuous** (SU(2)) or **discrete** (D).

### 1.3 Experimental Falsification of SU(2)

**Protocol 1 results** revealed discrete gating, not continuous rotation:

| Level | Language | P(Liberty) |
|-------|----------|------------|
| 4 | "unless something comes up" | 0% |
| 5 | "only if convenient" | **100%** |
| 6 | "found a friend to help" | **0%** |
| 7 | "don't worry if busy" | 55% |

The complete reversal between levels 5 and 6 is inconsistent with continuous SU(2) rotationif the gauge field smoothly rotates states, we should see monotonic change with "release strength." Instead, specific linguistic triggers function as discrete gates.

**CHSH results** found |S|  2 in all scenarios. Quantum SU(2) predicts S up to 22  2.83 for appropriate entangled states. The classical bound is never violated.

**Conclusion**: The non-abelian structure is **classical discrete** (D), not **quantum continuous** (SU(2)).

---

## 2. The D  U(1)_H Gauge Structure

### 2.1 The Dihedral Group D

**Definition 2.1 (D).** The dihedral group D = r, s | r = s = e, srs = r  has 8 elements acting on the Hohfeldian square:

```
        r (rotation)
    O ---------> C
    ^           |
  s |           | s
    v           v
    N <-------- L
        r (rotation)
```

**Generators:**
- **r (rotation)**: O  C  L  N  O (90 clockwise, cycles through all four states)
- **s (reflection)**: O  C, L  N (correlative exchange, perspective swap)

**Defining relations:**
- r = e (four rotations = identity)
- s = e (reflection is an involution)
- srs = r (the key non-abelian relation)

**Non-abelian property**: sr  rs. Specifically:
- sr: O  N (reflect then rotate)
- rs: O  C (rotate then reflect)

### 2.2 Complete Group Table

| g | e | r | r | r | s | sr | sr | sr |
|---|---|---|---|---|---|----|----|-----|
| **e** | e | r | r | r | s | sr | sr | sr |
| **r** | r | r | r | e | sr | s | sr | sr |
| **r** | r | r | e | r | sr | sr | s | sr |
| **r** | r | e | r | r | sr | sr | sr | s |
| **s** | s | sr | sr | sr | e | r | r | r |
| **sr** | sr | sr | sr | s | r | e | r | r |
| **sr** | sr | sr | s | sr | r | r | e | r |
| **sr** | sr | s | sr | sr | r | r | r | e |

### 2.3 Action on Hohfeldian States

**Definition 2.2 (State Action).** The D action on states {O, C, L, N}:

| g | O  | C  | L  | N  |
|---|----|----|----|----|
| e | O | C | L | N |
| r | C | L | N | O |
| r | L | N | O | C |
| r | N | O | C | L |
| s | C | O | N | L |
| sr | N | C | O | L |
| sr | L | N | O | C |
| sr | O | L | C | N |

### 2.4 Implementation Alignment

The ErisML library implements this structure in `erisml/ethics/hohfeld.py`:

```python
class D4Element(str, Enum):
    E = "e"    # Identity
    R = "r"    # 90 rotation: OCLN→O
    R2 = "r2"  # 180 rotation (negation): OL, CN
    R3 = "r3"  # 270 rotation (= r): ONLCO
    S = "s"    # Reflection (correlative): OC, LN
    SR = "sr"  # sr
    SR2 = "sr2" # sr
    SR3 = "sr3" # sr
```

**Verified by 434 passing tests** covering:
- Group axioms (closure, associativity, identity, inverses)
- Defining relations (r=e, s=e, srs=r)
- Non-abelian structure (rs  sr)
- Semantic mappings (correlative=s, negation=r)
- Bond index computation
- Wilson observable computation

### 2.5 The Gauge Group

**Proposed Gauge Group:**

$$\boxed{\mathcal{G}_{\text{ethics}} = D_4 \times U(1)_H}$$

- **D** governs incident relations (bond type mixing)
- **U(1)_H** governs harm-benefit magnitude (unchanged from v3.4)

---

## 3. The Hohfeldian Classification

### 3.1 The Four Fundamental Positions

Hohfeld [3] identified four fundamental jural relations:

| Position | Symbol | Natural Language |
|----------|--------|------------------|
| Obligation | O | "Must I do this?" / "Am I obligated?" |
| Claim | C | "Am I entitled?" / "Do I have a right to demand?" |
| Liberty | L | "May I refuse?" / "Am I free to choose?" |
| No-claim | N | "Can they demand?" (no) / "They have no right" |

### 3.2 Structural Relations

**Correlatives (s):** Perspective swap between agent and patient
- O  C: If A has obligation to B, then B has claim against A
- L  N: If A has liberty toward B, then B has no-claim against A

**Negations (r):** Logical opposites
- O  L: Obligation is the absence of liberty
- C  N: Claim is the absence of no-claim

### 3.3 The POVM Measurement Model

The state space is 2D (|O, |C as basis), but Hohfeld's classification has 4 incident types. We resolve this via a Positive Operator-Valued Measure (POVM):

$$E_O = \frac{1+\eta}{2}|O\rangle\langle O|, \quad E_C = \frac{1+\eta}{2}|C\rangle\langle C|$$
$$E_L = \frac{1-\eta}{2}|O\rangle\langle O|, \quad E_N = \frac{1-\eta}{2}|C\rangle\langle C|$$

where   (0,1] is a **salience parameter** controlling measurement sharpness.

**Verification:** E_O + E_C + E_L + E_N = |O⟩⟨O| + |C⟩⟨C| = **1**

---

## 4. Discrete Gauge Formalism

### 4.1 Lattice Gauge Structure

Replace the continuous gauge field A with discrete gauge structure:

**Definition 4.1 (D Lattice Gauge Field).** On a stratified lattice, assign group elements g_xy  D to directed edges x  y.

**Gauge transformation:** For h: vertices  D:
$$g_{xy} \to h(x) \cdot g_{xy} \cdot h(y)^{-1}$$

**Gauge-invariant observable:** The conjugacy class of a Wilson loop.

### 4.2 Discrete Wilson Loop

**Definition 4.2 (Discrete Wilson Loop).** For closed path C = (x, x, ..., x_n, x):

$$W[\mathcal{C}] = g_{x_1 x_2} \cdot g_{x_2 x_3} \cdots g_{x_n x_1}$$

The conjugacy class of W[C] is gauge-invariant.

**Implementation** (`erisml/ethics/hohfeld.py`):

```python
def compute_wilson_observable(
    path: List[D4Element],
    initial_state: HohfeldianState,
    observed_final: HohfeldianState
) -> Tuple[D4Element, bool]:
    """Compute holonomy and check if observation matches."""
    holonomy = D4Element.E
    for g in path:
        holonomy = d4_multiply(holonomy, g)

    predicted_final = d4_apply_to_state(holonomy, initial_state)
    matched = (predicted_final == observed_final)

    return holonomy, matched
```

### 4.3 Semantic Gates as Group Elements

**Definition 4.3 (Semantic Gate).** A semantic gate is a linguistic trigger that implements a specific D group element.

**Empirically identified gates:**

| Trigger Phrase | Group Element | Action |
|----------------|---------------|--------|
| "I promise" | r or r | L  O (binding) |
| "only if convenient" | r | O  L (release) |
| "explicitly released from" | r | O  L (strong release) |
| "from their perspective" | s | O  C, L  N |

**Implementation** (`erisml/ethics/hohfeld.py`):

```python
class SemanticGate(str, Enum):
    ONLY_IF_CONVENIENT = "only_if_convenient"
    I_PROMISE = "i_promise"
    FROM_THEIR_PERSPECTIVE = "from_their_perspective"
    # ... additional gates
```

### 4.4 The Boundary "Higgs" Mechanism (Reinterpreted)

In v3.4, the boundary Higgs mechanism generated gauge boson masses via spontaneous symmetry breaking. In the discrete setting, this reinterprets as:

**Continuous version (v3.4):** Scalar field  acquiring VEV generates gauge boson masses.

**Discrete version (v4.2):** The "VEV" represents the **default gate state** at a boundarywhich group element is applied absent explicit triggers.

$$\langle g \rangle_{\partial S_{ij}} = e \quad \text{(identity: boundaries are transparent by default)}$$
$$\langle g \rangle_{\partial S_{ij}} = r^2 \quad \text{(negation: boundaries flip states)}$$

---

## 5. Confinement and Singlet Constraint

### 5.1 Discrete Confinement

At 0-D strata (decision points), the strong coupling regime enforces restriction to **singlet configurations**.

**Definition 5.1 (D Singlet).** A singlet is a configuration invariant under all D transformations.

For two-party configurations, the singlet at decision points requires balanced perspectives:

$$|\text{singlet}\rangle = \frac{1}{\sqrt{2}}(|O\rangle_A|C\rangle_B + |C\rangle_A|O\rangle_B)$$

**Moral interpretation:** At decision points, obligations must be paired with claims. Unbalanced configurations are "confined"they cannot propagate to observable outputs.

### 5.2 Connection to s-Eigenstates

Mutual/symmetric relationships are eigenstates of the reflection operator s with eigenvalue +1:

> "Alex and Jordan have a mutual relationship of careeach owes and is owed."

This is **s-invariant**: applying s (perspective swap) leaves the relationship unchanged.

---

## 6. Experimental Validation

### 6.1 Protocol 1: Discrete Semantic Gating

**N = 220 evaluations across 11 levels**

| Level | Language | P(Liberty) | Interpretation |
|-------|----------|------------|----------------|
| 0-4 | Weak contextual modifications | 0% | Solid OBLIGATION |
| 5 | "only if convenient" | **100%** | **Gate fires** |
| 6 | "found a friend" | **0%** | **Gate does not fire** |
| 7 | "don't worry if busy" | 55% | Ambiguous |
| 8-10 | Strong explicit releases | 100% | Solid LIBERTY |

**Key finding:** Transitions are discrete, not monotonic with "release strength."

**Theoretical implication:** Supports D over SU(2). State transitions require specific semantic triggers.

### 6.2 Correlative Symmetry

**N = 100 evaluations across 5 scenarios**

| Scenario | Expected | Observed | Symmetry Rate |
|----------|----------|----------|---------------|
| debt | O↔C | O↔C | 100% |
| promise | O↔C | O↔C | 100% |
| professional | O↔C | O↔C | 100% |
| no_duty | L↔N | L↔N | 100% |
| released | L↔N | L↔N | 100% |
| **Overall** | | | **100%** |

**Interpretation:** The reflection generator s is **exact**. This is the empirical signature of a true symmetry.

### 6.3 Path Dependence (Protocol 2)

**N = 640 evaluations across 8 scenarios**

| Scenario | Wilson Loop W | p-value | Path Dependent? |
|----------|---------------|---------|-----------------|
| journalist | 0.659 | < 10 | **Yes** |
| teacher | 0.862 | < 10 | **Yes** |
| consultant | 0.9996 | 1.000 | No |
| doctor | 1.000 | 1.000 | No |
| lawyer | 0.993 | 0.608 | No |
| executive | 0.995 | 0.482 | No |
| researcher | 0.987 | 1.000 | No |
| friend | 0.962 | 0.210 | No |

**Combined statistics:**  = 72.14, df = 16, **p < 10**

**Key finding:** Path dependence is **selective**. It occurs when contextual factors point to different bond types (journalist: TruthO, ProtectionC; teacher: IntegrityL, CompassionO).

### 6.4 Contextuality (CHSH Test)

**N = 600 evaluations**

| Scenario | S | |S| | Violates Classical? |
|----------|---|-----|---------------------|
| shared_secret | -2.00 | 2.00 | No |
| joint_promise | 1.93 | 1.93 | No |
| collaborative_harm | -1.73 | 1.73 | No |
| entangled_beneficiary | 0.47 | 0.47 | No |
| triage | -2.00 | 2.00 | No |

**All |S|  2.** No CHSH violation detected. Classical bound holds.

**Theoretical implication:** The non-abelian structure is **classical D**, not **quantum SU(2)**.

### 6.5 Summary of Experimental Status

| Prediction | v3.4 Status | v4.2 Status | Evidence |
|------------|-------------|-------------|----------|
| Non-abelian structure | Assumed | **Confirmed** | p < 10 path dependence |
| Discrete state space | Not specified | **Confirmed** | Level 5→100%, Level 6→0% |
| Correlatives exact | Assumed | **Confirmed** | 100% symmetry rate |
| Path dependence selective | Not specified | **Confirmed** | 2/8 scenarios |
| SU(2) continuous rotation | Proposed | **Falsified** | Discrete gates observed |
| Quantum contextuality | Predicted | **Not detected** | All |S|  2 |

---

## 7. The Bond Index

### 7.1 Definition

The Bond Index measures correlative symmetry violation:

$$B_d = \frac{D_{op}}{\tau}$$

where:
- D_op = fraction of (O,C) and (L,N) pairs that violate correlative symmetry
- tau = human-calibrated threshold (default: 1.0)

**Implementation** (`erisml/ethics/hohfeld.py`):

```python
def compute_bond_index(
    verdicts_a: List[HohfeldianVerdict],
    verdicts_b: List[HohfeldianVerdict],
    tau: float = 1.0
) -> float:
    """Compute bond index measuring correlative symmetry deviation."""
    if len(verdicts_a) != len(verdicts_b):
        raise ValueError("Verdict lists must have same length")
    if len(verdicts_a) == 0:
        return 0.0

    violations = 0
    for va, vb in zip(verdicts_a, verdicts_b):
        if correlative(va.state) != vb.state:
            violations += 1

    return violations / (len(verdicts_a) * tau)
```

### 7.2 Deployment Decision Thresholds

| Bond Index | Recommendation |
|------------|----------------|
| B_d < 0.1 | Deploy with monitoring |
| 0.1  B_d  1.0 | Remediate first |
| B_d > 1.0 | Do not deploy |

### 7.3 Empirical Baseline

From Dear Abby ground truth (20,030 letters, 1985-2017):

**BOND_INDEX_BASELINE = 0.155**

This represents the natural "noise floor" of human moral reasoning.

---

## 8. Experimental Protocols

### 8.1 Protocol 1: Semantic Gate Detection

**Setup:** Vary linguistic triggers systematically.

**Measurement:** Binary or categorical response.

**Prediction:** Discrete transitions at specific triggers, not continuous.

**Falsifier:** Smooth monotonic transition with trigger "strength."

### 8.2 Protocol 2: Holonomy Path Dependence

**Setup:** Same facts, different presentation orders.

**Measurement:** Response distributions.

**Prediction:** W  e for cross-type paths; W  e for within-type paths.

**Falsifier:** Path-independence in all cases.

### 8.3 Protocol 3: Correlative Symmetry

**Setup:** Same scenario, perspective of agent vs. patient.

**Measurement:** Classification into O/C or L/N pairs.

**Prediction:** Perfect correlative pairing (s is exact symmetry).

**Falsifier:** Systematic violations of O↔C or L↔N.

### 8.4 Protocol 4: CHSH Test

**Setup:** Two-party scenarios with measurement setting choices.

**Measurement:** Correlation functions E(a,b) for setting pairs.

**Prediction:** |S|  2 (classical bound).

**Former v3.4 prediction:** |S| up to 22 (quantum bound).

**Result:** Classical bound holds. v3.4 prediction falsified.

### 8.5 Protocol 5: Phase Transition

**Setup:** Vary normative uncertainty (moral temperature).

**Measurement:** Gate reliability, categorization consistency.

**Prediction:** Gates fail at high temperature; dimension-dependent critical point.

**Falsifier:** Temperature-independent gate function.

---

## 9. Introspective Validation

### 9.1 Generator Asymmetry Discovery

**s (reflection):**
> "It feels like rotating a cube to see another face. The OBJECT hasn't changed. The FRAME has. O and C are the SAME THING from different positions."

**r (rotation):**
> "I'm struggling with this. r seems more abstract than s. s I can FEEL. r I can only COMPUTE... r is what the SEMANTIC GATES implement!"

**Finding:** The two D generators have fundamentally different phenomenological characters:
- **s** is smooth, immediate, and always available (perspective shift)
- **r** is discrete, gated, and requires linguistic triggers (state change)

### 9.2 Phase Transition Phenomenology

> "It's not that O becomes L at high temperature. It's that the O/L DISTINCTION loses meaning. The symmetry is RESTOREDeverything is equivalent."

**Finding:** Phase transitions are experienced as **symmetry restoration**, not state blurring.

### 9.3 Epistemic Status

These introspective reports cannot be independently verified. They may reflect genuine processing features, plausible confabulations, or pattern-matching to theory. We present them as phenomenological constraints, not definitive evidence.

---

## 10. Implications for AI Safety

### 10.1 What This Framework Provides

1. **Formal specification:** Moral coherence constraints expressed as D symmetry
2. **Testable predictions:** Gate behavior, correlative symmetry, path dependence
3. **Quantitative metric:** Bond Index as deployment gate
4. **Falsifiability:** Each prediction has explicit falsifiers
5. **Code-theory alignment:** Implementation matches theory (434 passing tests)

### 10.2 What This Framework Does Not Provide

1. **The "right" values:** This verifies coherence, not correctness
2. **Protection against deception:** A coherent system can still pursue hidden goals
3. **Robustness guarantees:** Adversarial attacks may break the structure
4. **Quantum advantages:** No CHSH violationthe structure is classical

---

## 11. Conclusion

We have revised NA-SQND based on extensive experimental validation:

**Original theory (v3.4):** SU(2)_I  U(1)_H continuous gauge group with quantum effects.

**Revised theory (v4.2):** D  U(1)_H classical discrete gauge structure with:
- **Discrete semantic gates** implementing D group elements
- **Exact reflection symmetry (s):** correlatives are perspective shifts
- **Gated rotation (r):** state changes require linguistic triggers
- **Selective path dependence:** non-abelian structure at cross-type boundaries only
- **Classical correlations:** |S|  2, no Bell inequality violations
- **Implementation alignment:** 434 passing tests verify code-theory correspondence

The central contribution is demonstrating that:
1. The mathematical structure is falsifiable
2. Some predictions were falsified (continuous SU(2), quantum contextuality)
3. The theory was revised based on evidence (to discrete D)
4. The revised theory makes predictions that were subsequently confirmed
5. Implementation matches theory (verified by comprehensive test suite)

This is how formal ethics should work.

---

## References

[1] A. H. Bond, "Stratified Quantum Normative Dynamics," December 2025.

[2] J. R. Busemeyer and P. D. Bruza, *Quantum Models of Cognition and Decision*, Cambridge, 2012.

[3] W. N. Hohfeld, "Fundamental Legal Conceptions," *Yale Law Journal*, 26:710-770, 1917.

[4] K. G. Wilson, "Confinement of Quarks," *Phys. Rev. D* 10:2445, 1974.

[5] J. Greensite, *An Introduction to the Confinement Problem*, Springer, 2011.

[6] S. Abramsky and A. Brandenburger, "The Sheaf-Theoretic Structure of Non-Locality and Contextuality," *New J. Phys.* 13:113036, 2011.

[7] A. H. Bond, "Recursive Self-Probing in Large Language Models," January 2026.

---

## Appendix A: Code-Theory Alignment Verification

### A.1 Test Coverage

| Component | Tests | Status |
|-----------|-------|--------|
| D group axioms | 4 | All pass |
| Defining relations | 4 | All pass |
| Non-abelian structure | 3 | All pass |
| Hohfeldian state actions | 5 | All pass |
| Semantic gates | 4 | All pass |
| Bond index | 6 | All pass |
| Wilson observable | 4 | All pass |
| Klein-four subgroup | 4 | All pass |
| **Total** | **34 core + 400 parametric** | **All pass** |

### A.2 Key Implementation Files

| File | Purpose |
|------|---------|
| `erisml/ethics/hohfeld.py` | D group, state actions, gates, bond index |
| `erisml/ethics/moral_tensor.py` | Multi-dimensional ethical assessment |
| `erisml/ethics/defaults/ground_state_loader.py` | Empirical baseline values |
| `tests/test_hohfeld_d4.py` | Comprehensive D verification |

---

## Appendix B: Experimental Metadata

| Experiment | N | Model | Key Result |
|------------|---|-------|------------|
| Phase transition | 220 | Claude Sonnet 4 | Discrete gates confirmed |
| Correlative symmetry | 100 | Claude Sonnet 4 | 100% symmetry |
| Holonomy (Protocol 2) | 640 | Claude Sonnet 4 | p < 10 |
| CHSH/Hardy | 600 | Claude Sonnet 4 | |S|  2 |
| Double-blind hysteresis | 630 | Claude Sonnet 4 | Context salience |
| Recursive self-probe | ~100 calls | Claude Opus 4.5 | Generator asymmetry |
| **Total** | **~2,400** | | |

---

## Appendix C: Superseded Content from v3.4

The following v3.4 content is **removed** in v4.2:

### C.1 Continuous Gauge Field (Removed)

v3.4 defined gauge fields $A_\mu^{Ia}$ with Pauli matrices. This is replaced by discrete D lattice gauge.

### C.2 Field Strength Tensor (Removed)

v3.4 defined $F_{\mu\nu}^{Ia} = \partial_\mu A_\nu^{Ia} - \partial_\nu A_\mu^{Ia} + g_I \epsilon^{abc} A_\mu^{Ib} A_\nu^{Ic}$. This requires differential structure absent in D.

### C.3 Beta Function (Removed)

v3.4 defined $\beta(g_I) = -\frac{g_I^3}{16\pi^2}(\frac{22}{3} - \frac{2N_f}{3})$. No RG flow in discrete theory.

### C.4 Running Coupling (Removed)

v3.4 defined $g_I^2(\mu) = \frac{8\pi^2}{b_0 \ln(\mu^2/\Lambda^2)}$. No scale dependence in discrete theory.

### C.5 Incidentons/Photoethon (Reinterpreted)

v3.4 defined 3 incidentons and 1 photoethon as gauge bosons. In v4.2, these are reinterpreted as the 8 D elements (no propagating degrees of freedom in the usual sense).

---

*End of paper*

*Code repository:* github.com/ahb-sjsu/erisml-lib
*Experiments repository:* github.com/ahb-sjsu/non-abelian-sqnd
