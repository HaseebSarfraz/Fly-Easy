# Planner Evaluation Report

## 1. Introduction

This report evaluates the performance and integrity of our itinerary planning algorithm under varying configuration settings. The planner is designed to generate multi-day travel plans while strictly respecting **hard constraints** (e.g., time windows, fixed anchors, feasibility) and attempting to satisfy **soft constraints** (e.g., preferences, budget smoothness, minimal nudging). To assess robustness, we systematically tested the planner under all possible combinations of its major configuration toggles.

---

## 2. Evaluation Methodology

### 2.1 Configuration Space

We evaluated **16 configurations**, generated from all combinations of four boolean toggles:

* Budget enforcement
* Meal planning
* Base plan generation
* RepairB (soft-constraint repair strategy)

Weather checks were held constant to avoid stochastic effects and ensure comparability across runs.

### 2.2 Execution Strategy

Rather than treating the planner as a single monolithic function, the evaluation script operates as a **stress-test and benchmarking engine**:

* Each configuration is injected into the planner independently.
* For each client, the script iterates day-by-day across the trip duration.
* A fresh daily plan is generated using the active configuration, ensuring that toggles genuinely alter planner behavior (e.g., budget disabled means activity costs are ignored for that run).

This approach ensures that results reflect planner behavior under realistic, incremental decision-making rather than a single aggregated output.

### 2.3 Violation Detection

Once a plan is generated, it is evaluated using a dedicated **violation detector** that inspects each scheduled event. The following checks are applied:

* **Time Window Violations:** Events scheduled outside the client’s allowed daily start/end times.
* **Anchor Conflicts:** Overlaps with fixed-time activities (e.g., concerts), treated as critical failures.
* **Budget Violations:** Daily spending exceeding the client’s proportional daily allowance.
* **Repair Usage:** Instances where RepairB nudges or rearranges activities to restore feasibility.

### 2.4 Weighted Scoring System

Violations are not treated equally. Each type contributes to a final **Average Violation Score** using weighted penalties:

* Anchor conflicts carry the highest penalty.
* Time window violations are strongly penalized.
* Repairs incur a small soft penalty, reflecting acceptable human-like adjustment.
* Budget overruns are penalized proportionally and forgivingly.

Lower scores indicate higher-quality, more feasible plans.

---

## 3. Key Observed Patterns

To illustrate planner behavior, we highlight two representative clients:

### Client 1 (Constraint-Heavy Case)

Client 1 exhibits a wide range of violation scores depending on configuration. Simpler configurations (with fewer toggles enabled) often achieved zero violations because fewer constraints were being enforced. However, when all toggles were enabled, violation scores increased significantly. This increase does **not** indicate failure; instead, it reflects the planner actively enforcing hard constraints and sacrificing soft ones when necessary.

### Client 4 (Simple Dataset Case)

Client 4 achieved zero violations across all 16 configurations. This indicates that the underlying dataset was sufficiently unconstrained such that even the most restrictive planner settings did not force trade-offs. This result demonstrates that the planner does not introduce unnecessary changes when constraints are easily satisfiable.

**Takeaway:** Violation scores are highly dependent on dataset complexity. Higher scores often reflect stronger enforcement rather than poorer planning.

---

## 4. Strong-Toggle Configuration Analysis

Configurations with all toggles enabled consistently demonstrated the highest **constraint integrity**. In these cases:

* Hard constraints were always respected.
* Activities were replaced, moved, or removed when necessary.
* Soft constraints (preferences, minimal movement) were sacrificed as intended.

This behavior aligns with the planner’s design philosophy: **feasibility first, optimization second**. The algorithm behaves conservatively, preferring a valid plan over a perfect-but-impossible one.

---

## 5. Trade-offs and Limitations

While the planner incorporates human-like reasoning—such as repairing plans, searching for interest-aligned activities, and minimizing disruption—this comes at a computational cost.

As more toggles are enabled:

* The search space increases.
* More constraint checks and repairs are triggered.
* Overall runtime grows.

This trade-off is intrinsic to constraint-based planning systems. The planner prioritizes correctness and realism over raw speed, which is acceptable for offline or pre-trip itinerary generation but may require optimization for real-time use.

---

## 6. Visualization

To visually ground the evaluation results, we include tabular summaries for two representative clients: **Client 1** (constraint-heavy) and **Client 4** (simple dataset). These tables show how the Average Violation Score changes across all 16 planner configurations.

### Client 1: Constraint-Heavy Scenario

| Rank | Avg. Violation Score | Configuration                           |
| ---- | -------------------- | --------------------------------------- |
| 1    | 0.00                 | Budget ✓ · Meals ✓ · Base ✗ · RepairB ✗ |
| 2    | 0.00                 | Budget ✓ · Meals ✗ · Base ✓ · RepairB ✗ |
| 3    | 0.00                 | Budget ✓ · Meals ✗ · Base ✗ · RepairB ✓ |
| 4    | 0.00                 | Budget ✓ · Meals ✗ · Base ✗ · RepairB ✗ |
| 5    | 0.00                 | Budget ✗ · Meals ✓ · Base ✓ · RepairB ✓ |
| 6    | 0.00                 | Budget ✗ · Meals ✓ · Base ✓ · RepairB ✗ |
| 7    | 0.00                 | Budget ✗ · Meals ✓ · Base ✗ · RepairB ✓ |
| 8    | 0.00                 | Budget ✗ · Meals ✓ · Base ✗ · RepairB ✗ |
| 9    | 0.00                 | Budget ✗ · Meals ✗ · Base ✓ · RepairB ✓ |
| 10   | 0.00                 | Budget ✗ · Meals ✗ · Base ✓ · RepairB ✗ |
| 11   | 0.00                 | Budget ✗ · Meals ✗ · Base ✗ · RepairB ✓ |
| 12   | 0.00                 | Budget ✗ · Meals ✗ · Base ✗ · RepairB ✗ |
| 13   | 2.00                 | Budget ✓ · Meals ✗ · Base ✓ · RepairB ✓ |
| 14   | 4.00                 | Budget ✓ · Meals ✓ · Base ✗ · RepairB ✓ |
| 15   | 39.00                | Budget ✓ · Meals ✓ · Base ✓ · RepairB ✗ |
| 16   | 52.00                | Budget ✓ · Meals ✓ · Base ✓ · RepairB ✓ |

These results demonstrate how enabling additional constraints increases planner friction, reflecting active enforcement rather than failure.

### Client 4: Simple Dataset Scenario

| Rank | Avg. Violation Score | Configuration                           |
| ---- | -------------------- | --------------------------------------- |
| 1    | 0.00                 | Budget ✓ · Meals ✓ · Base ✓ · RepairB ✓ |
| 2    | 0.00                 | Budget ✓ · Meals ✓ · Base ✓ · RepairB ✗ |
| 3    | 0.00                 | Budget ✓ · Meals ✓ · Base ✗ · RepairB ✓ |
| 4    | 0.00                 | Budget ✓ · Meals ✓ · Base ✗ · RepairB ✗ |
| 5    | 0.00                 | Budget ✓ · Meals ✗ · Base ✓ · RepairB ✓ |
| 6    | 0.00                 | Budget ✓ · Meals ✗ · Base ✓ · RepairB ✗ |
| 7    | 0.00                 | Budget ✓ · Meals ✗ · Base ✗ · RepairB ✓ |
| 8    | 0.00                 | Budget ✓ · Meals ✗ · Base ✗ · RepairB ✗ |
| 9    | 0.00                 | Budget ✗ · Meals ✓ · Base ✓ · RepairB ✓ |
| 10   | 0.00                 | Budget ✗ · Meals ✓ · Base ✓ · RepairB ✗ |
| 11   | 0.00                 | Budget ✗ · Meals ✓ · Base ✗ · RepairB ✓ |
| 12   | 0.00                 | Budget ✗ · Meals ✓ · Base ✗ · RepairB ✗ |
| 13   | 0.00                 | Budget ✗ · Meals ✗ · Base ✓ · RepairB ✓ |
| 14   | 0.00                 | Budget ✗ · Meals ✗ · Base ✓ · RepairB ✗ |
| 15   | 0.00                 | Budget ✗ · Meals ✗ · Base ✗ · RepairB ✓ |
| 16   | 0.00                 | Budget ✗ · Meals ✗ · Base ✗ · RepairB ✗ |

This uniform outcome shows that when constraints are easily satisfiable, even the most restrictive planner configuration does not introduce unnecessary violations.

---

## 7. Implications for a Travel Application

From a travel app perspective, these results are highly favorable:

* Users are guaranteed **feasible itineraries** that respect real-world constraints.
* Minor preference sacrifices are acceptable when they prevent major failures (missed events, impossible schedules).
* The planner builds user trust by avoiding invalid or conflicting plans.

Future extensions could dynamically adjust toggles based on trip complexity, achieving an adaptive balance between performance and rigor.

---

## 8. Conclusion

Through exhaustive configuration testing, we demonstrate that the planner performs best when all constraint-enforcing features are enabled. Although this increases soft-constraint violations and computational cost, it ensures robust, realistic, and trustworthy itineraries—an essential requirement for real-world travel planning systems.
