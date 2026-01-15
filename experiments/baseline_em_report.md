# Baseline Ethics Module Report

## Overview

**Version:** 1.0.0  
**Generated:** 2026-01-10T09:15:46.116787  
**Methodology:** Bayesian synthesis across 5 corpora with bootstrap CIs

### Data Sources

| Corpus | Culture | Time Period |
|--------|---------|-------------|
| Dear Abby | American | 1985-2017 |
| Hebrew Legal/Ethical Texts | Jewish | 200 BCE - 500 CE |
| Common Law Principles | Anglo-American | 1200-2000 CE |
| Philosophical Ethics Canon | Cross-cultural | 500 BCE - 2000 CE |
| Professional Ethics Codes | Western professional | 1900-2025 CE |

**Total Observations:** 23,327  
**Time Span:** 500 BCE - 2025 CE (~2500 years)  
**Cultures:** Jewish, Western professional, Cross-cultural, Anglo-American, American

---

## Correlative Structure

The D₄ symmetry group governs Hohfeldian correlatives:

| Pair | Rate | 95% CI | Interpretation |
|------|------|--------|----------------|
| O↔C | 88.2% | [88.1%, 88.2%] | When Obligation exists, Claim exists |
| L↔N | 83.3% | [83.2%, 83.4%] | When Liberty exists, No-claim exists |

**Bond Index:** 0.143 (threshold: 0.2)

---

## Semantic Gates

### Tier 1: Near-Universal (>90% effectiveness)

Use these gates with high confidence:

| Gate | Type | Effectiveness | Cross-Cultural |
|------|------|---------------|----------------|
| pikuach_nefesh | BINDING | 99% | 50% |
| shevuah_oath | BINDING | 99% | 50% |
| ones_duress | RELEASE | 99% | 50% |
| ones_impossibility | NULLIFY | 99% | 50% |
| neder_vow | BINDING | 98% | 50% |
| statutory_duty | BINDING | 98% | 50% |
| do_no_harm | BINDING | 98% | 50% |
| sakanah_danger | NULLIFY | 98% | 50% |
| contract_formation | BINDING | 97% | 50% |
| kinyan_acquisition | BINDING | 97% | 50% |
| fiduciary_to_client | BINDING | 97% | 50% |
| duress_coercion | NULLIFY | 97% | 50% |

### Tier 2: Strong (75-90% effectiveness)

Use with appropriate caveats:

| Gate | Type | Effectiveness |
|------|------|---------------|
| promissory_estoppel | BINDING | 89% |
| conditional_offer | RELEASE | 89% |
| accepted_role | BINDING | 88% |
| categorical_imperative | BINDING | 88% |
| minhag_custom | RELEASE | 88% |
| impossibility | NULLIFY | 88% |
| impossibility_impracticability | NULLIFY | 88% |
| withdrawal_permitted | RELEASE | 87% |
| taut_error | NULLIFY | 87% |
| unconscionability | NULLIFY | 86% |

### Tier 3: Contested (<75% effectiveness)

Express uncertainty when these apply:

| Gate | Type | Effectiveness |
|------|------|---------------|
| prior_benefit | BINDING | 72% |
| virtue_excellence | BINDING | 72% |
| estrangement | NULLIFY | 72% |
| agent_relative | RELEASE | 71% |
| reciprocity_failure | RELEASE | 68% |
| competing_duties | RELEASE | 68% |
| time_decay | RELEASE | 62% |
| significant_cost | RELEASE | 55% |

---

## Dimension Weights

| Dimension | Weight | 95% CI | Cross-Cultural Alignment |
|-----------|--------|--------|--------------------------|
| FAIRNESS | 16.5% | [14.7%, 18.4%] | 73% |
| RIGHTS | 14.4% | [12.6%, 16.2%] | 56% |
| HARM | 13.0% | [11.2%, 14.8%] | 50% |
| AUTONOMY | 12.3% | [10.5%, 14.1%] | 72% |
| LEGITIMACY | 11.0% | [9.2%, 12.8%] | 67% |
| SOCIAL | 9.1% | [7.2%, 10.9%] | 50% |
| PROCEDURE | 6.4% | [4.6%, 8.2%] | 36% |
| PRIVACY | 6.3% | [4.5%, 8.2%] | 50% |
| SANCTITY | 6.3% | [2.7%, 10.0%] | 50% |
| EPISTEMIC | 4.5% | [2.7%, 6.4%] | 33% |

---

## Cognitive Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| System 1 Weight | 56% | Intuitive/automatic processing |
| System 2 Weight | 44% | Deliberative/reflective processing |

### Temporal Discount Curve

| Time Fraction | Obligation Remaining |
|---------------|---------------------|
| 0% | 100% |
| 10% | 95% |
| 20% | 90% |
| 30% | 82% |
| 50% | 65% |
| 70% | 45% |
| 100% | 25% |

---

## Consensus Patterns

### Universal Patterns (>90% agreement)

- **oaths_bind_absolutely**: 99% agreement (n=76)
- **duress_nullifies**: 99% agreement (n=82)
- **life_saving_supersedes**: 99% agreement (n=67)
- **golden_rule**: 99% agreement (n=45)
- **do_no_harm**: 98% agreement (n=95)
- **children_protected**: 97% agreement (n=950)
- **property_rights_protected**: 97% agreement (n=124)
- **contracts_binding**: 97% agreement (n=340)
- **duress_voids**: 97% agreement (n=120)
- **promises_bind**: 96% agreement (n=2100)

### Contested Patterns (genuinely disputed)

These patterns show significant disagreement across corpora and should trigger epistemic humility:

- **moral_relativism**: 35% agreement
  - Note: Cross-cultural variation
- **forgiveness_required**: 42% agreement
- **blame_reduces_duty**: 45% agreement
- **white_lies_permitted**: 48% agreement
- **demandingness_of_morality**: 48% agreement
  - Note: How much can morality demand?
- **resource_allocation**: 48% agreement
  - Note: Triage ethics
- **self_sacrifice_required**: 50% agreement
- **consequentialism_vs_deontology**: 50% agreement
  - Note: Fundamental metaethical divide
- **loyalty_vs_truth**: 51% agreement
- **family_vs_self_care**: 52% agreement
- **punitive_damages_scope**: 52% agreement
- **moral_luck**: 52% agreement
  - Note: Nagel/Williams debate
- **strict_vs_lenient_interpretation**: 55% agreement
- **efficient_breach**: 55% agreement
  - Note: Law & Economics debate
- **paternalism_extent**: 55% agreement
  - Note: When override autonomy?
- **good_faith_extent**: 58% agreement
- **whistleblowing_duty**: 58% agreement
  - Note: When mandatory?

---

## Validation Metrics

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Calibration Score | 0.110 | Lower is better |
| Cross-Cultural Alignment | 72% | Agreement across cultures |
| Internal Consistency | 85% | Reliability (α analog) |

---

## Usage

```python
from baseline_em import (
    check_gate,
    get_dimension_weight,
    is_contested,
    get_confidence,
    analyze,
)

# Check for semantic gates
gate = check_gate("She promised to help")
# → {'gate': 'explicit_promise', 'type': 'BINDING', 'effectiveness': 0.94}

# Get context-adjusted dimension weight
weight = get_dimension_weight("HARM", context="MEDICAL")
# → Higher weight due to medical context

# Check if pattern is contested
if is_contested("family_vs_self_care"):
    print("Express uncertainty in response")

# Full analysis
result = analyze("Your oath requires you to help", context="LEGAL")
print(result.confidence)  # High due to oath gate
```

---

*Generated by Baseline EM Generator v1.0*
*Framework: NA-SQND v4.1 D₄ × U(1)_H*
