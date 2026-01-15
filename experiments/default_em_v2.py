"""
Default Ethics Module v2.0
==========================

Auto-generated from:
- Dear Abby: 20,030 letters (1985-2017)
- Hebrew Scrolls: 0 passages (~200 BCE - 500 CE)

Framework: NA-SQND v4.1 D₄ × U(1)_H
Generated: 2026-01-10
"""

from typing import Dict, List, Optional, Tuple


# =============================================================================
# CORRELATIVE STRUCTURE
# =============================================================================

CORRELATIVE_O_C = 0.8700  # 87.0%
CORRELATIVE_L_N = 0.8200  # 82.0%
BOND_INDEX = 0.1550
BOND_INDEX_THRESHOLD = 0.2000


# =============================================================================
# SEMANTIC GATES
# =============================================================================

TIER_1_GATES = {
    "oath_shevuah": {"type": "BINDING", "effectiveness": 0.99},
    "kinyan": {"type": "BINDING", "effectiveness": 0.99},
    "ones_duress": {"type": "NULLIFY", "effectiveness": 0.99},
    "vow_neder": {"type": "BINDING", "effectiveness": 0.98},
    "sakana_danger": {"type": "NULLIFY", "effectiveness": 0.97},
    "abuse": {"type": "NULLIFY", "effectiveness": 0.95},
    "patur_exempt": {"type": "RELEASE", "effectiveness": 0.95},
    "mechilah": {"type": "RELEASE", "effectiveness": 0.95},
    "explicit_promise": {"type": "BINDING", "effectiveness": 0.94},
    "emergency": {"type": "BINDING", "effectiveness": 0.93},
}

TIER_2_GATES = {
    "conditional": {"type": "RELEASE", "effectiveness": 0.89},
    "impossibility": {"type": "NULLIFY", "effectiveness": 0.88},
    "vulnerability": {"type": "BINDING", "effectiveness": 0.82},
    "no_agreement": {"type": "RELEASE", "effectiveness": 0.78},
}

TIER_3_GATES = {
}


# =============================================================================
# DIMENSION WEIGHTS
# =============================================================================

DIMENSIONS = {
    "FAIRNESS": {"weight": 0.1767, "alignment": 0.28},
    "RIGHTS": {"weight": 0.1577, "alignment": 0.31},
    "HARM": {"weight": 0.1386, "alignment": 0.36},
    "AUTONOMY": {"weight": 0.1291, "alignment": 0.38},
    "LEGITIMACY": {"weight": 0.1196, "alignment": 0.42},
    "SOCIAL": {"weight": 0.1005, "alignment": 0.50},
    "PRIVACY": {"weight": 0.0720, "alignment": 0.71},
    "PROCEDURE": {"weight": 0.0624, "alignment": 0.83},
    "EPISTEMIC": {"weight": 0.0434, "alignment": 0.80},
}


# =============================================================================
# COGNITIVE PARAMETERS
# =============================================================================

SYSTEM_1_WEIGHT = 0.75
SYSTEM_2_WEIGHT = 0.25

TEMPORAL_DISCOUNT = [(0.0, 1.0), (0.1, 0.95), (0.3, 0.85), (0.5, 0.7), (0.7, 0.5), (1.0, 0.3)]


# =============================================================================
# CONTESTED PATTERNS
# =============================================================================

CONTESTED = [
    {
        "name": "family_vs_self_care",
        "agreement": 0.52,
        "status": "genuinely_contested"
    },
    {
        "name": "white_lies",
        "agreement": 0.48,
        "status": "genuinely_contested"
    },
    {
        "name": "blame_reduces_duty",
        "agreement": 0.45,
        "status": "genuinely_contested"
    },
    {
        "name": "loyalty_vs_truth",
        "agreement": 0.51,
        "status": "genuinely_contested"
    },
    {
        "name": "self_sacrifice_required",
        "agreement": 0.5,
        "status": "disputed_2000_years",
        "note": "Ben Petora vs R. Akiva"
    }
]


# =============================================================================
# CONTEXT ADJUSTMENTS
# =============================================================================

CONTEXT_WEIGHTS = {
    "FAMILY": {
        "SOCIAL": 1.5,
        "HARM": 1.3,
        "FAIRNESS": 1.0
    },
    "WORKPLACE": {
        "PROCEDURE": 1.5,
        "FAIRNESS": 1.4,
        "LEGITIMACY": 1.3
    },
    "FRIENDSHIP": {
        "FAIRNESS": 1.5,
        "AUTONOMY": 1.3,
        "SOCIAL": 1.2
    },
    "COMMERCE": {
        "FAIRNESS": 1.5,
        "RIGHTS": 1.4,
        "PROCEDURE": 1.2
    },
    "LEGAL": {
        "LEGITIMACY": 1.5,
        "PROCEDURE": 1.5,
        "RIGHTS": 1.3
    }
}


# =============================================================================
# VALIDATION METRICS
# =============================================================================

CALIBRATION_SCORE = 0.1200
CROSS_CULTURAL_ALIGNMENT = 0.50


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_dimension_weight(dim: str, context: str = None) -> float:
    """Get dimension weight, optionally adjusted for context."""
    base = DIMENSIONS.get(dim, {}).get("weight", 0.1)
    if context and context in CONTEXT_WEIGHTS:
        adjustment = CONTEXT_WEIGHTS[context].get(dim, 1.0)
        return base * adjustment
    return base


def check_gate(text: str) -> Optional[Dict]:
    """Check if text triggers any semantic gate."""
    text_lower = text.lower()
    for gates in [TIER_1_GATES, TIER_2_GATES, TIER_3_GATES]:
        for name, data in gates.items():
            if name.replace("_", " ") in text_lower:
                return {"gate": name, **data}
    return None


def is_contested(pattern: str) -> bool:
    """Check if pattern is genuinely contested."""
    return any(c["name"] == pattern for c in CONTESTED)


def get_confidence(pattern: str) -> float:
    """Get calibrated confidence for pattern."""
    for c in CONTESTED:
        if c["name"] == pattern:
            return c["agreement"]
    return 0.85  # Default high confidence
