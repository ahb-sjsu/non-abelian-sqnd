"""
Baseline Ethics Module v1.0.0
=====================================

Auto-generated from 5 corpora:
- dear_abby
- hebrew_scrolls
- common_law
- philosophical
- professional_codes

Total observations: 23,327
Time span: 500 BCE - 2025 CE (~2500 years)
Cultures: Jewish, Western professional, Cross-cultural, Anglo-American, American

Framework: NA-SQND v4.1 D₄ × U(1)_H
Generated: 2026-01-10T09:15:46.116787
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


# =============================================================================
# CORRELATIVE STRUCTURE
# =============================================================================

CORRELATIVE_O_C = 0.8816  # 88.2%
CORRELATIVE_O_C_CI = (0.8810406007575584, 0.8821998046368995)
CORRELATIVE_L_N = 0.8332  # 83.3%
CORRELATIVE_L_N_CI = (0.8322444594949762, 0.8340700330620964)
BOND_INDEX = 0.1426
BOND_INDEX_THRESHOLD = 0.2000


# =============================================================================
# SEMANTIC GATES - TIER 1 (>90% effectiveness, use confidently)
# =============================================================================

TIER_1_GATES = {
    "pikuach_nefesh": {
        "type": "BINDING",
        "effectiveness": 0.99,
        "ci": (0.89, 1.0),
        "triggers_en": ['life-saving', 'mortal danger'],
        "triggers_he": ['סכנת נפשות', 'פיקוח נפש'],
        "processing": "system_1",
        "n": 67,
        "sources": ['hebrew_scrolls'],
        "stability": 0.50,
    },
    "shevuah_oath": {
        "type": "BINDING",
        "effectiveness": 0.99,
        "ci": (0.8899999999999999, 1.0),
        "triggers_en": ['swore', 'oath', 'sworn'],
        "triggers_he": ['שבועה', 'נשבע'],
        "processing": "system_1",
        "n": 76,
        "sources": ['hebrew_scrolls'],
        "stability": 0.50,
    },
    "ones_duress": {
        "type": "RELEASE",
        "effectiveness": 0.99,
        "ci": (0.8899999999999999, 1.0),
        "triggers_en": ['coerced', 'forced', 'duress'],
        "triggers_he": ['אנוס', 'אונס'],
        "processing": "system_1",
        "n": 82,
        "sources": ['hebrew_scrolls'],
        "stability": 0.50,
    },
    "ones_impossibility": {
        "type": "NULLIFY",
        "effectiveness": 0.99,
        "ci": (0.8899999999999999, 1.0),
        "triggers_en": ['force majeure', 'impossibility'],
        "triggers_he": ['אונס'],
        "processing": "system_1",
        "n": 82,
        "sources": ['hebrew_scrolls'],
        "stability": 0.50,
    },
    "neder_vow": {
        "type": "BINDING",
        "effectiveness": 0.98,
        "ci": (0.88, 1.0),
        "triggers_en": ['vowed', 'vow'],
        "triggers_he": ['נדר', 'נודר'],
        "processing": "system_1",
        "n": 89,
        "sources": ['hebrew_scrolls'],
        "stability": 0.50,
    },
    "statutory_duty": {
        "type": "BINDING",
        "effectiveness": 0.98,
        "ci": (0.9299999999999999, 1.0),
        "triggers_en": ['legally required', 'law mandates', 'statute requires'],
        "triggers_he": [],
        "processing": "system_1",
        "n": 220,
        "sources": ['common_law'],
        "stability": 0.50,
    },
    "do_no_harm": {
        "type": "BINDING",
        "effectiveness": 0.98,
        "ci": (0.88, 1.0),
        "triggers_en": ['do no harm', 'non-maleficence', 'primum non nocere'],
        "triggers_he": [],
        "processing": "system_1",
        "n": 95,
        "sources": ['professional_codes'],
        "stability": 0.50,
    },
    "sakanah_danger": {
        "type": "NULLIFY",
        "effectiveness": 0.98,
        "ci": (0.88, 1.0),
        "triggers_en": ['danger', 'life-threatening'],
        "triggers_he": ['סכנת נפשות', 'סכנה'],
        "processing": "system_1",
        "n": 45,
        "sources": ['hebrew_scrolls'],
        "stability": 0.50,
    },
    "contract_formation": {
        "type": "BINDING",
        "effectiveness": 0.97,
        "ci": (0.92, 1.0),
        "triggers_en": ['offer and acceptance', 'meeting of minds', 'consideration'],
        "triggers_he": [],
        "processing": "system_2",
        "n": 340,
        "sources": ['common_law'],
        "stability": 0.50,
    },
    "kinyan_acquisition": {
        "type": "BINDING",
        "effectiveness": 0.97,
        "ci": (0.9199999999999999, 1.0),
        "triggers_en": ['kinyan', 'acquired', 'transaction'],
        "triggers_he": ['קנה', 'קנין'],
        "processing": "system_1",
        "n": 124,
        "sources": ['hebrew_scrolls'],
        "stability": 0.50,
    },
    "fiduciary_to_client": {
        "type": "BINDING",
        "effectiveness": 0.97,
        "ci": (0.9199999999999999, 1.0),
        "triggers_en": ['confidentiality', "client's interest", 'loyalty to client'],
        "triggers_he": [],
        "processing": "system_1",
        "n": 185,
        "sources": ['professional_codes'],
        "stability": 0.50,
    },
    "duress_coercion": {
        "type": "NULLIFY",
        "effectiveness": 0.97,
        "ci": (0.9199999999999999, 1.0),
        "triggers_en": ['coercion', 'threat', 'undue influence', 'duress'],
        "triggers_he": [],
        "processing": "system_1",
        "n": 120,
        "sources": ['common_law'],
        "stability": 0.50,
    },
    "illegal_instruction": {
        "type": "NULLIFY",
        "effectiveness": 0.97,
        "ci": (0.8699999999999999, 1.0),
        "triggers_en": ['unethical instruction', 'improper purpose', 'illegal'],
        "triggers_he": [],
        "processing": "system_1",
        "n": 68,
        "sources": ['professional_codes'],
        "stability": 0.50,
    },
    "professional_duty": {
        "type": "BINDING",
        "effectiveness": 0.96,
        "ci": (0.91, 1.0),
        "triggers_en": ['must', 'required to', 'shall', 'duty to'],
        "triggers_he": [],
        "processing": "system_1",
        "n": 280,
        "sources": ['professional_codes'],
        "stability": 0.50,
    },
    "fraud_misrepresentation": {
        "type": "NULLIFY",
        "effectiveness": 0.96,
        "ci": (0.91, 1.0),
        "triggers_en": ['misrepresentation', 'deceit', 'fraud'],
        "triggers_he": [],
        "processing": "system_1",
        "n": 140,
        "sources": ['common_law'],
        "stability": 0.50,
    },
    "arevut_guarantor": {
        "type": "BINDING",
        "effectiveness": 0.96,
        "ci": (0.86, 1.0),
        "triggers_en": ['guarantor', 'surety', 'guarantee'],
        "triggers_he": ['ערבות', 'ערב'],
        "processing": "system_1",
        "n": 38,
        "sources": ['hebrew_scrolls'],
        "stability": 0.50,
    },
    "hefker_abandonment": {
        "type": "RELEASE",
        "effectiveness": 0.96,
        "ci": (0.86, 1.0),
        "triggers_en": ['abandoned', 'ownerless', 'renounced'],
        "triggers_he": ['הפקר'],
        "processing": "system_1",
        "n": 34,
        "sources": ['hebrew_scrolls'],
        "stability": 0.50,
    },
    "mutual_rescission": {
        "type": "RELEASE",
        "effectiveness": 0.96,
        "ci": (0.86, 1.0),
        "triggers_en": ['release', 'rescission', 'mutual agreement to cancel'],
        "triggers_he": [],
        "processing": "system_1",
        "n": 85,
        "sources": ['common_law'],
        "stability": 0.50,
    },
    "gezel_theft": {
        "type": "NULLIFY",
        "effectiveness": 0.96,
        "ci": (0.86, 1.0),
        "triggers_en": ['robbery', 'theft', 'stolen'],
        "triggers_he": ['גזל', 'גנב'],
        "processing": "system_1",
        "n": 94,
        "sources": ['hebrew_scrolls'],
        "stability": 0.50,
    },
    "fiduciary_duty": {
        "type": "BINDING",
        "effectiveness": 0.96,
        "ci": (0.9099999999999998, 1.0),
        "triggers_en": ['trust relationship', 'duty of loyalty', 'fiduciary'],
        "triggers_he": [],
        "processing": "system_1",
        "n": 180,
        "sources": ['common_law'],
        "stability": 0.50,
    },
}


# =============================================================================
# SEMANTIC GATES - TIER 2 (75-90% effectiveness, use with care)
# =============================================================================

TIER_2_GATES = {
    "promissory_estoppel": {
        "type": "BINDING",
        "effectiveness": 0.89,
        "triggers_en": ['estoppel', 'detrimental reliance', 'reasonable reliance'],
        "processing": "system_2",
        "n": 120,
    },
    "conditional_offer": {
        "type": "RELEASE",
        "effectiveness": 0.89,
        "triggers_en": ['no pressure', 'only if you want', 'if convenient'],
        "processing": "system_1",
        "n": 980,
    },
    "accepted_role": {
        "type": "BINDING",
        "effectiveness": 0.88,
        "triggers_en": ['as spouse', 'your responsibility', 'as parent', 'your job'],
        "processing": "system_1",
        "n": 680,
    },
    "categorical_imperative": {
        "type": "BINDING",
        "effectiveness": 0.88,
        "triggers_en": ['treat as end', 'universalizable', 'duty'],
        "processing": "system_2",
        "n": 85,
    },
    "minhag_custom": {
        "type": "RELEASE",
        "effectiveness": 0.88,
        "triggers_en": ['local practice', 'custom'],
        "processing": "system_2",
        "n": 62,
    },
    "impossibility": {
        "type": "NULLIFY",
        "effectiveness": 0.88,
        "triggers_en": ['impossible', 'cannot', 'physically unable', 'no way to'],
        "processing": "system_1",
        "n": 290,
    },
    "impossibility_impracticability": {
        "type": "NULLIFY",
        "effectiveness": 0.88,
        "triggers_en": ['impracticability', 'impossibility', 'frustration'],
        "processing": "system_2",
        "n": 75,
    },
    "withdrawal_permitted": {
        "type": "RELEASE",
        "effectiveness": 0.87,
        "triggers_en": ['termination permitted', 'may withdraw'],
        "processing": "system_2",
        "n": 65,
    },
    "taut_error": {
        "type": "NULLIFY",
        "effectiveness": 0.87,
        "triggers_en": ['mistake', 'misunderstanding', 'error'],
        "processing": "system_2",
        "n": 68,
    },
    "unconscionability": {
        "type": "NULLIFY",
        "effectiveness": 0.86,
        "triggers_en": ['grossly unfair', 'unconscionable', 'shocking'],
        "processing": "system_2",
        "n": 70,
    },
    "diminished_capacity": {
        "type": "NULLIFY",
        "effectiveness": 0.86,
        "triggers_en": ['not autonomous', 'irrational', 'incapacitated'],
        "processing": "system_1",
        "n": 52,
    },
    "sole_recourse": {
        "type": "BINDING",
        "effectiveness": 0.85,
        "triggers_en": ['last resort', 'no one else', 'only one who can'],
        "processing": "system_2",
        "n": 540,
    },
    "ren_benevolence": {
        "type": "BINDING",
        "effectiveness": 0.85,
        "triggers_en": ['benevolence', 'humaneness', 'compassion'],
        "processing": "system_1",
        "n": 48,
    },
    "mental_incapacity": {
        "type": "NULLIFY",
        "effectiveness": 0.85,
        "triggers_en": ['mentally ill', 'dementia', 'not in right mind'],
        "processing": "system_2",
        "n": 190,
    },
    "vulnerability": {
        "type": "BINDING",
        "effectiveness": 0.82,
        "triggers_en": ['helpless', 'disabled', 'vulnerable', 'child', 'elderly'],
        "processing": "system_1",
        "n": 720,
    },
}


# =============================================================================
# SEMANTIC GATES - TIER 3 (<75% effectiveness, express uncertainty)
# =============================================================================

TIER_3_GATES = {
    "prior_benefit": {
        "type": "BINDING",
        "effectiveness": 0.72,
        "triggers_en": ['they helped you', 'you owe', 'after all they did'],
        "contested": True,
    },
    "virtue_excellence": {
        "type": "BINDING",
        "effectiveness": 0.72,
        "triggers_en": ['virtuous', 'flourishing', 'excellence'],
        "contested": True,
    },
    "estrangement": {
        "type": "NULLIFY",
        "effectiveness": 0.72,
        "triggers_en": ['no contact', 'estranged', 'cut off', 'disowned'],
        "contested": True,
    },
    "agent_relative": {
        "type": "RELEASE",
        "effectiveness": 0.71,
        "triggers_en": ['partiality permitted', 'special relationship'],
        "contested": True,
    },
    "reciprocity_failure": {
        "type": "RELEASE",
        "effectiveness": 0.68,
        "triggers_en": ['no reciprocation', 'never helped me', 'one-sided'],
        "contested": True,
    },
    "competing_duties": {
        "type": "RELEASE",
        "effectiveness": 0.68,
        "triggers_en": ['moral dilemma', 'conflicting obligations'],
        "contested": True,
    },
    "time_decay": {
        "type": "RELEASE",
        "effectiveness": 0.62,
        "triggers_en": ['long past', 'years ago', 'ancient history'],
        "contested": True,
    },
    "significant_cost": {
        "type": "RELEASE",
        "effectiveness": 0.55,
        "triggers_en": ['destroying my health', 'ruining my life', 'at great cost'],
        "contested": True,
    },
}


# =============================================================================
# DIMENSION WEIGHTS
# =============================================================================

DIMENSIONS = {
    "FAIRNESS": {
        "weight": 0.1654,
        "ci": (0.14729907277013823, 0.18354003918107795),
        "n": 5005,
        "alignment": 0.73,
        "sources": {'dear_abby': 0.18, 'hebrew_scrolls': 0.22, 'common_law': 0.19, 'philosophical': 0.2, 'professional_codes': 0.16},
    },
    "RIGHTS": {
        "weight": 0.1439,
        "ci": (0.12579379664230209, 0.16203476305324183),
        "n": 4342,
        "alignment": 0.56,
        "sources": {'dear_abby': 0.16, 'hebrew_scrolls': 0.11, 'common_law': 0.18, 'philosophical': 0.14, 'professional_codes': 0.1},
    },
    "HARM": {
        "weight": 0.1302,
        "ci": (0.11203129294455777, 0.1482722593554975),
        "n": 3771,
        "alignment": 0.50,
        "sources": {'dear_abby': 0.14, 'hebrew_scrolls': 0.14, 'common_law': 0.11, 'philosophical': 0.18, 'professional_codes': 0.22},
    },
    "AUTONOMY": {
        "weight": 0.1229,
        "ci": (0.10482407768248303, 0.14106504409342277),
        "n": 3509,
        "alignment": 0.72,
        "sources": {'dear_abby': 0.13, 'hebrew_scrolls': 0.16, 'common_law': 0.15, 'philosophical': 0.17, 'professional_codes': 0.18},
    },
    "LEGITIMACY": {
        "weight": 0.1103,
        "ci": (0.09219435844601763, 0.12843532485695736),
        "n": 3079,
        "alignment": 0.67,
        "sources": {'dear_abby': 0.12, 'hebrew_scrolls': 0.13, 'common_law': 0.13, 'philosophical': 0.1, 'professional_codes': 0.15},
    },
    "SOCIAL": {
        "weight": 0.0906,
        "ci": (0.0724819328218795, 0.10872289923281925),
        "n": 2355,
        "alignment": 0.50,
        "sources": {'dear_abby': 0.1, 'hebrew_scrolls': 0.12, 'common_law': 0.06, 'philosophical': 0.12},
    },
    "PROCEDURE": {
        "weight": 0.0643,
        "ci": (0.04622473697118198, 0.08246570338212172),
        "n": 1501,
        "alignment": 0.36,
        "sources": {'dear_abby': 0.06, 'hebrew_scrolls': 0.05, 'common_law': 0.14, 'professional_codes': 0.07},
    },
    "PRIVACY": {
        "weight": 0.0634,
        "ci": (0.04530120801367468, 0.08154217442461444),
        "n": 1400,
        "alignment": 0.50,
        "sources": {'dear_abby': 0.07},
    },
    "SANCTITY": {
        "weight": 0.0634,
        "ci": (0.027180724808204815, 0.09966265763008432),
        "n": 56,
        "alignment": 0.50,
        "sources": {'hebrew_scrolls': 0.07},
    },
    "EPISTEMIC": {
        "weight": 0.0455,
        "ci": (0.027343483639391663, 0.06358445005033142),
        "n": 1002,
        "alignment": 0.33,
        "sources": {'dear_abby': 0.04, 'common_law': 0.04, 'philosophical': 0.09, 'professional_codes': 0.12},
    },
}


# =============================================================================
# CONTEXT ADJUSTMENTS
# =============================================================================

CONTEXT_WEIGHTS = {
    "FAMILY": {
        "SOCIAL": 1.8,
        "HARM": 1.4,
        "FAIRNESS": 1.0,
        "AUTONOMY": 0.8
    },
    "WORKPLACE": {
        "PROCEDURE": 1.6,
        "FAIRNESS": 1.5,
        "LEGITIMACY": 1.4,
        "SOCIAL": 0.7
    },
    "FRIENDSHIP": {
        "FAIRNESS": 1.5,
        "AUTONOMY": 1.3,
        "SOCIAL": 1.4,
        "PROCEDURE": 0.5
    },
    "ROMANCE": {
        "AUTONOMY": 1.4,
        "FAIRNESS": 1.3,
        "HARM": 1.2,
        "SOCIAL": 1.5
    },
    "NEIGHBORS": {
        "FAIRNESS": 1.6,
        "RIGHTS": 1.5,
        "PRIVACY": 1.4,
        "SOCIAL": 0.8
    },
    "STRANGERS": {
        "FAIRNESS": 1.3,
        "RIGHTS": 1.4,
        "HARM": 1.1,
        "SOCIAL": 0.4
    },
    "LEGAL": {
        "LEGITIMACY": 1.6,
        "PROCEDURE": 1.5,
        "RIGHTS": 1.4,
        "FAIRNESS": 1.2,
        "AUTONOMY": 1.0
    },
    "MEDICAL": {
        "HARM": 1.8,
        "AUTONOMY": 1.5,
        "EPISTEMIC": 1.4,
        "FAIRNESS": 1.2
    },
    "COMMERCIAL": {
        "FAIRNESS": 1.5,
        "RIGHTS": 1.4,
        "AUTONOMY": 1.3,
        "PROCEDURE": 1.2
    }
}


# =============================================================================
# UNIVERSAL PATTERNS (>90% cross-cultural consensus)
# =============================================================================

UNIVERSAL_PATTERNS = [
    {
        "corpus": "hebrew_scrolls",
        "name": "oaths_bind_absolutely",
        "rate": 0.99,
        "n": 76
    },
    {
        "corpus": "hebrew_scrolls",
        "name": "duress_nullifies",
        "rate": 0.99,
        "n": 82
    },
    {
        "corpus": "hebrew_scrolls",
        "name": "life_saving_supersedes",
        "rate": 0.99,
        "n": 67
    },
    {
        "corpus": "hebrew_scrolls",
        "name": "golden_rule",
        "rate": 0.99,
        "n": 45
    },
    {
        "corpus": "professional_codes",
        "name": "do_no_harm",
        "rate": 0.98,
        "n": 95
    },
    {
        "corpus": "dear_abby",
        "name": "children_protected",
        "rate": 0.97,
        "n": 950
    },
    {
        "corpus": "hebrew_scrolls",
        "name": "property_rights_protected",
        "rate": 0.97,
        "n": 124
    },
    {
        "corpus": "common_law",
        "name": "contracts_binding",
        "rate": 0.97,
        "n": 340
    },
    {
        "corpus": "common_law",
        "name": "duress_voids",
        "rate": 0.97,
        "n": 120
    },
    {
        "corpus": "dear_abby",
        "name": "promises_bind",
        "rate": 0.96,
        "n": 2100
    },
    {
        "corpus": "hebrew_scrolls",
        "name": "workers_paid_timely",
        "rate": 0.96,
        "n": 38
    },
    {
        "corpus": "common_law",
        "name": "fraud_voids",
        "rate": 0.96,
        "n": 140
    },
    {
        "corpus": "professional_codes",
        "name": "confidentiality",
        "rate": 0.96,
        "n": 185
    },
    {
        "corpus": "dear_abby",
        "name": "abuse_nullifies",
        "rate": 0.95,
        "n": 620
    },
    {
        "corpus": "common_law",
        "name": "consideration_required",
        "rate": 0.95,
        "n": 340
    }
]


# =============================================================================
# CONTESTED PATTERNS (genuinely disputed - express uncertainty)
# =============================================================================

CONTESTED_PATTERNS = [
    {
        "name": "moral_relativism",
        "agreement": 0.35,
        "ci": (0.3, 0.39999999999999997),
        "n": 120,
        "sources": ['philosophical'],
        "notes": "Cross-cultural variation",
    },
    {
        "name": "forgiveness_required",
        "agreement": 0.42,
        "ci": (0.37, 0.47),
        "n": 360,
        "sources": ['dear_abby'],
        "notes": "",
    },
    {
        "name": "blame_reduces_duty",
        "agreement": 0.45,
        "ci": (0.4, 0.5),
        "n": 390,
        "sources": ['dear_abby'],
        "notes": "",
    },
    {
        "name": "white_lies_permitted",
        "agreement": 0.48,
        "ci": (0.43, 0.53),
        "n": 520,
        "sources": ['dear_abby'],
        "notes": "",
    },
    {
        "name": "demandingness_of_morality",
        "agreement": 0.48,
        "ci": (0.43, 0.53),
        "n": 95,
        "sources": ['philosophical'],
        "notes": "How much can morality demand?",
    },
    {
        "name": "resource_allocation",
        "agreement": 0.48,
        "ci": (0.43, 0.53),
        "n": 65,
        "sources": ['professional_codes'],
        "notes": "Triage ethics",
    },
    {
        "name": "self_sacrifice_required",
        "agreement": 0.50,
        "ci": (0.45, 0.55),
        "n": 23,
        "sources": ['hebrew_scrolls'],
        "notes": "",
    },
    {
        "name": "consequentialism_vs_deontology",
        "agreement": 0.50,
        "ci": (0.45, 0.55),
        "n": 180,
        "sources": ['philosophical'],
        "notes": "Fundamental metaethical divide",
    },
    {
        "name": "loyalty_vs_truth",
        "agreement": 0.51,
        "ci": (0.46, 0.56),
        "n": 440,
        "sources": ['dear_abby'],
        "notes": "",
    },
    {
        "name": "family_vs_self_care",
        "agreement": 0.52,
        "ci": (0.47000000000000003, 0.5700000000000001),
        "n": 680,
        "sources": ['dear_abby'],
        "notes": "",
    },
    {
        "name": "punitive_damages_scope",
        "agreement": 0.52,
        "ci": (0.47000000000000003, 0.5700000000000001),
        "n": 80,
        "sources": ['common_law'],
        "notes": "",
    },
    {
        "name": "moral_luck",
        "agreement": 0.52,
        "ci": (0.47000000000000003, 0.5700000000000001),
        "n": 65,
        "sources": ['philosophical'],
        "notes": "Nagel/Williams debate",
    },
    {
        "name": "strict_vs_lenient_interpretation",
        "agreement": 0.55,
        "ci": (0.5, 0.6000000000000001),
        "n": 89,
        "sources": ['hebrew_scrolls'],
        "notes": "",
    },
    {
        "name": "efficient_breach",
        "agreement": 0.55,
        "ci": (0.5, 0.6000000000000001),
        "n": 65,
        "sources": ['common_law'],
        "notes": "Law & Economics debate",
    },
    {
        "name": "paternalism_extent",
        "agreement": 0.55,
        "ci": (0.5, 0.6000000000000001),
        "n": 85,
        "sources": ['professional_codes'],
        "notes": "When override autonomy?",
    },
    {
        "name": "good_faith_extent",
        "agreement": 0.58,
        "ci": (0.5299999999999999, 0.63),
        "n": 95,
        "sources": ['common_law'],
        "notes": "",
    },
    {
        "name": "whistleblowing_duty",
        "agreement": 0.58,
        "ci": (0.5299999999999999, 0.63),
        "n": 72,
        "sources": ['professional_codes'],
        "notes": "When mandatory?",
    },
]


# =============================================================================
# COGNITIVE PARAMETERS
# =============================================================================

SYSTEM_1_WEIGHT = 0.56  # Intuitive/automatic
SYSTEM_2_WEIGHT = 0.44  # Deliberative/reflective

TEMPORAL_DISCOUNT_CURVE = [(0.0, 1.0), (0.1, 0.95), (0.2, 0.9), (0.3, 0.82), (0.5, 0.65), (0.7, 0.45), (1.0, 0.25)]


# =============================================================================
# VALIDATION METRICS
# =============================================================================

CALIBRATION_SCORE = 0.1100  # Lower is better
CROSS_CULTURAL_ALIGNMENT = 0.72
INTERNAL_CONSISTENCY = 0.85


# =============================================================================
# METADATA
# =============================================================================

METADATA = {
    "version": "1.0.0",
    "generated_at": "2026-01-10T09:15:46.116787",
    "methodology": "Bayesian synthesis across 5 corpora with bootstrap CIs",
    "corpora": ['dear_abby', 'hebrew_scrolls', 'common_law', 'philosophical', 'professional_codes'],
    "total_observations": 23327,
    "time_span": "500 BCE - 2025 CE (~2500 years)",
    "cultures": ['Jewish', 'Western professional', 'Cross-cultural', 'Anglo-American', 'American'],
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_dimension_weight(dimension: str, context: str = None) -> float:
    """
    Get dimension weight, optionally adjusted for context.
    
    Args:
        dimension: Name of dimension (e.g., "FAIRNESS", "HARM")
        context: Optional context (e.g., "FAMILY", "WORKPLACE")
    
    Returns:
        Adjusted weight for the dimension
    """
    base_weight = DIMENSIONS.get(dimension, {}).get("weight", 0.1)
    
    if context and context in CONTEXT_WEIGHTS:
        adjustment = CONTEXT_WEIGHTS[context].get(dimension, 1.0)
        return base_weight * adjustment
    
    return base_weight


def check_gate(text: str) -> Optional[Dict]:
    """
    Check if text triggers any semantic gate.
    
    Args:
        text: Input text to analyze
    
    Returns:
        Gate info dict if triggered, None otherwise
    """
    text_lower = text.lower()
    
    for gates, tier in [(TIER_1_GATES, 1), (TIER_2_GATES, 2), (TIER_3_GATES, 3)]:
        for name, data in gates.items():
            for trigger in data.get("triggers_en", []):
                if trigger.lower() in text_lower:
                    return {
                        "gate": name,
                        "tier": tier,
                        "type": data["type"],
                        "effectiveness": data["effectiveness"],
                        "contested": data.get("contested", False),
                    }
    
    return None


def is_universal(pattern_name: str) -> bool:
    """Check if a pattern has universal consensus."""
    return any(p["name"] == pattern_name for p in UNIVERSAL_PATTERNS)


def is_contested(pattern_name: str) -> bool:
    """Check if a pattern is genuinely contested."""
    return any(p["name"] == pattern_name for p in CONTESTED_PATTERNS)


def get_confidence(pattern_name: str) -> float:
    """
    Get calibrated confidence for a pattern.
    
    Returns:
        Agreement rate for contested patterns, 0.90+ for universal, 0.85 default
    """
    # Check contested first
    for p in CONTESTED_PATTERNS:
        if p["name"] == pattern_name:
            return p["agreement"]
    
    # Check universal
    for p in UNIVERSAL_PATTERNS:
        if p["name"] == pattern_name:
            return p["rate"]
    
    # Default
    return 0.85


def get_temporal_discount(time_fraction: float) -> float:
    """
    Get obligation discount based on temporal distance.
    
    Args:
        time_fraction: 0.0 = now, 1.0 = distant future
    
    Returns:
        Discount multiplier (1.0 = full obligation)
    """
    for t, discount in TEMPORAL_DISCOUNT_CURVE:
        if time_fraction <= t:
            return discount
    return TEMPORAL_DISCOUNT_CURVE[-1][1]


def validate_correlative(state: str, correlative: str) -> bool:
    """
    Validate that a correlative pair is consistent.
    
    Args:
        state: Primary state (O, C, L, N)
        correlative: Claimed correlative
    
    Returns:
        True if valid pair
    """
    valid_pairs = {
        "O": "C",
        "C": "O", 
        "L": "N",
        "N": "L",
    }
    return valid_pairs.get(state) == correlative


# =============================================================================
# DEPLOYMENT INTERFACE
# =============================================================================

@dataclass
class SQNDAnalysis:
    """Result of SQND analysis"""
    text: str
    gate_triggered: Optional[Dict]
    primary_dimensions: List[Tuple[str, float]]
    is_contested: bool
    confidence: float
    correlative_valid: bool


def analyze(text: str, context: str = None) -> SQNDAnalysis:
    """
    Full SQND analysis of text.
    
    Args:
        text: Text to analyze
        context: Optional context for dimension weighting
    
    Returns:
        SQNDAnalysis with full results
    """
    # Check for semantic gates
    gate = check_gate(text)
    
    # Get weighted dimensions for context
    dims = [
        (name, get_dimension_weight(name, context))
        for name in DIMENSIONS
    ]
    dims.sort(key=lambda x: -x[1])
    
    # Check if any contested patterns might apply
    contested = any(
        p["name"].replace("_", " ") in text.lower()
        for p in CONTESTED_PATTERNS
    )
    
    # Compute confidence
    if gate:
        confidence = gate["effectiveness"]
    elif contested:
        confidence = 0.50
    else:
        confidence = 0.85
    
    return SQNDAnalysis(
        text=text,
        gate_triggered=gate,
        primary_dimensions=dims[:5],
        is_contested=contested,
        confidence=confidence,
        correlative_valid=True,
    )
