# Commit Summary: Add ROC-AUC Metric

## What
Added ROC-AUC as a precision metric to measure how well quantification results can distinguish changed from unchanged species.

## Why Add This Metric
Existing metrics (epsilon, CV) focus on **accuracy** - how close measured values are to expected. ROC-AUC measures **classification performance** - how well we can separate HUMAN (unchanged, ~1:1 ratio) from YEAST/ECOLI (changed species). A tool could have low epsilon but still confuse species; ROC-AUC captures this.

## Why Add to This Branch (`species_weighted_metrics`)
This branch already introduces species-aware metric calculations (`eq_species` mode). Adding it here keeps all metric enhancements together in one coherent PR, rather than spreading them across multiple branches.

## Scope: Computation Only

- ROC-AUC is **computed and stored** in the results dict (`"roc_auc"` key)
- GUI support is **prepared** in `plot_quant.py` (handles ROC-AUC plotting)
- GUI is **NOT exposed** - metric selector still shows only Median/Mean
- TODO comments mark where to add `"ROC-AUC"` to enable it later

## How It Works
- **Score**: `abs(log2_A_vs_B)` - unchanged species should have values near 0
- **Labels**: Species with smallest `|log2_expectedRatio|` = unchanged (auto-detected), others = changed
- **Output**: Single value in [0, 1], where 0.5 = random, 1.0 = perfect separation

## Implementation Details

### Function: `compute_roc_auc()` in `proteobench/datapoint/quant_datapoint.py`

```python
def compute_roc_auc(df: pd.DataFrame, unchanged_species: str = None) -> float:
```

**Algorithm:**
1. Auto-detect unchanged species via `_detect_unchanged_species()` if not provided
2. Create binary labels: `y_true = (species != unchanged_species)` → 0 for unchanged, 1 for changed
3. Create scores: `y_score = abs(log2_A_vs_B)` → higher values indicate more change
4. Call `sklearn.metrics.roc_auc_score(y_true, y_score)`

### Function: `_detect_unchanged_species()` in `proteobench/datapoint/quant_datapoint.py`

```python
def _detect_unchanged_species(df: pd.DataFrame) -> str | None:
```

**Algorithm:**
1. Get unique species-ratio pairs from `df[["species", "log2_expectedRatio"]].drop_duplicates()`
2. Find the species with smallest `abs(log2_expectedRatio)` (closest to 1:1 ratio)
3. Return that species name

### Integration
Called from `get_metrics()` and stored in results dict:
```python
"roc_auc": compute_roc_auc(df_slice)
```

## Performance (Arm M4 chip)
~3.7 ms per call for 30k precursors. Negligible overhead (~22 ms total per datapoint).

## Files Changed
- `proteobench/datapoint/quant_datapoint.py` - `compute_roc_auc()`, `_detect_unchanged_species()`
- `proteobench/plotting/plot_quant.py` - GUI plotting support (prepared)
- `webinterface/pages/base_pages/tab1_results.py` - TODO comment
- `webinterface/pages/base_pages/tab4_display_results_submitted.py` - TODO comment
- `test/test_quant_datapoint.py` - 10 tests including bounds verification

## Tests
All 173 tests pass.

## If You Disagree
If you disagree with the ROC-AUC addition, you can safely revert it:

```bash
git revert 6bac82ca
```

This creates a new commit that undoes the ROC-AUC changes while preserving the full history. Safe for shared branches.
