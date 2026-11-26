"""
Naming a datapoint, and describing what sets it apart from its tool's other runs.
"""

from typing import Dict, List, Optional, Tuple
import re

import numpy as np
import pandas as pd

from proteobench.plotting.plot_generator_denovo.ranking import rank_within_tools


# Every curve from one tool is drawn in that tool's colour, so a tool submitted several times
# -- one datapoint per decoding strategy, say -- would otherwise draw identically coloured,
# identically named lines that no legend entry or hover text could tell apart. Label each line
# by whatever actually differs between that tool's submissions. Separating them visually is the
# job of `shade_within_tool`, which varies lightness: a dash cycle runs out after six styles,
# and one tool's submissions already reach fifteen.
# Tried in order, most workflow-defining first, so the shortest label that disambiguates wins.
WORKFLOW_LABEL_FIELDS = ("decoding_strategy", "n_beams", "checkpoint", "software_version")

# A run refined by a second model records both checkpoints in one field, base model first.
CHECKPOINT_SEPARATOR = ";"

# Product names for refinement models, keyed by the leading token of their checkpoint name.
# A refinement checkpoint that is not listed still gets its own clause, just unnamed.
REFINEMENT_MODEL_NAMES = {"instanovoplus": "InstaNovo+"}


def _is_blank(value: object) -> bool:
    """Whether a datapoint field carries no usable value."""
    if value is None:
        return True
    if isinstance(value, float) and np.isnan(value):
        return True
    return str(value).strip() in ("", "nan", "None", "<NA>")


def _display_value(value: object) -> str:
    """
    Render a datapoint field for a hover box or an on-plot label.

    A blank in any row turns the whole column float, so an integer parameter such as a beam
    count arrives here as ``10.0`` and would read that way on the plot. Whole floats are
    therefore shown without their decimal, the same coercion `_format_label_field` undoes for
    the parameter-style labels.
    """
    if _is_blank(value):
        return "\u2014"
    if isinstance(value, float) and float(value).is_integer():
        return str(int(value))
    return str(value)


def _format_label_field(field: str, value: object) -> str:
    """Render one distinguishing field for use inside a workflow label."""
    text = str(value).strip()
    if field == "n_beams":
        # A blank in any row makes the whole column float, which would read "10.0 beams".
        try:
            count = float(text)
        except ValueError:
            return f"{text} beams"
        return f"{count:g} beam" if count == 1 else f"{count:g} beams"
    if field == "software_version":
        return f"v{text.lstrip('v')}"
    return text


def _split_checkpoint(value: object) -> tuple:
    """
    Split a checkpoint field into the base model and any refinement stages.

    A run that post-processes its predictions with a second model records both, separated by
    ``;`` -- the base model first. Reported separately so a refined run reads as a refinement
    of its base rather than as an unrelated pair of checkpoints.
    """
    stages = [stage.strip() for stage in str(value).split(CHECKPOINT_SEPARATOR) if stage.strip()]
    return (stages[0] if stages else ""), stages[1:]


def _refinement_model_name(checkpoint: str) -> Optional[str]:
    """The product name of a refinement model, from its checkpoint name."""
    token = re.split(r"[-_ ]", checkpoint.strip(), maxsplit=1)[0].lower()
    return REFINEMENT_MODEL_NAMES.get(token)


def _refinement_clause(refinements: List[str]) -> str:
    """Render the trailing "with ... refinement" clause for any post-processing stages."""
    if not refinements:
        return ""
    rendered = []
    for checkpoint in refinements:
        name = _refinement_model_name(checkpoint)
        rendered.append(f"{name} refinement ({checkpoint})" if name else f"refinement ({checkpoint})")
    return " with " + " and ".join(rendered)


def _display_software_name(software: str, checkpoint: object) -> str:
    """
    The name to show for a datapoint, which is not always its ``software_name``.

    A run whose only checkpoint is a refinement model is that model working on its own rather
    than the tool that usually calls it: InstaNovo+ diffusion sampling is recorded under
    ``software_name`` "InstaNovo", but it is not InstaNovo. Only the displayed name changes --
    colour, marker and grouping still follow ``software_name``, which keeps such a run with the
    rest of its project's results and avoids inventing a tool name the palettes do not know.
    """
    if _is_blank(checkpoint):
        return software
    base, refinements = _split_checkpoint(checkpoint)
    if refinements:
        return software  # a base model that was refined; the base model still names the run
    return _refinement_model_name(base) or software


def _render_workflow_label(software: str, parts: List[str], suffix: str) -> str:
    """Assemble a workflow label from the tool name, its distinguishing fields and any suffix."""
    if not parts:
        return f"{software}{suffix}"
    return f"{software} ({', '.join(parts)}){suffix}"


def _display_name_series(result_df: pd.DataFrame, software_names: pd.Series) -> pd.Series:
    """
    The tool name to show per datapoint, which is not always its ``software_name``.

    Grouping stays on ``software_name`` -- runs of one project are compared against each other --
    but the name shown can differ per row, so a standalone refinement model is not mislabelled as
    the tool that usually drives it.

    Parameters
    ----------
    result_df : pd.DataFrame
        Datapoints to name. ``checkpoint`` is used when present.
    software_names : pd.Series
        ``software_name`` as strings, aligned to ``result_df.index``.

    Returns
    -------
    pd.Series
        Display names aligned to ``result_df.index``.
    """
    if "checkpoint" not in result_df.columns:
        return software_names.copy()
    return pd.Series(
        [_display_software_name(name, checkpoint) for name, checkpoint in zip(software_names, result_df["checkpoint"])],
        index=result_df.index,
        dtype=object,
    )


def _variant_fields(
    result_df: pd.DataFrame, software_names: pd.Series, display_names: pd.Series
) -> Tuple[Dict[object, List[str]], Dict[object, str]]:
    """
    Collect the fields that tell each tool's own submissions apart.

    A tool that appears once has nothing to tell apart and gets nothing. For a tool submitted
    several times, a field earns a place only when that tool's own submissions differ on it:
    a field that is constant across them would lengthen every label without separating anything.

    Parameters
    ----------
    result_df : pd.DataFrame
        Datapoints to inspect. Any of :data:`WORKFLOW_LABEL_FIELDS` are used when present.
    software_names : pd.Series
        ``software_name`` as strings, which decides the grouping.
    display_names : pd.Series
        The name shown per datapoint, used only to test whether the fields gathered so far
        already separate a tool's rows.

    Returns
    -------
    tuple of dict
        Rendered field values per index, and the trailing refinement clause per index.
    """
    parts: Dict[object, List[str]] = {idx: [] for idx in result_df.index}
    suffixes: Dict[object, str] = {idx: "" for idx in result_df.index}

    for _, group in result_df.groupby(software_names, sort=False):
        if len(group) < 2:
            continue

        for field in WORKFLOW_LABEL_FIELDS:
            if field not in group.columns:
                continue
            values = group[field]
            # A field only earns a place in the label if this tool's own submissions differ
            # on it; two distinct non-blank values is the minimum that can separate two rows.
            if len({str(v).strip() for v in values if not _is_blank(v)}) < 2:
                continue
            for idx, value in values.items():
                if _is_blank(value):
                    continue
                if field == "checkpoint":
                    # The base model belongs with the other settings; refinement stages read
                    # as a clause after them, so a refined run names what refined it.
                    base, refinements = _split_checkpoint(value)
                    if base:
                        parts[idx].append(base)
                    suffixes[idx] = _refinement_clause(refinements)
                else:
                    parts[idx].append(_format_label_field(field, value))
            rendered = {_render_workflow_label(display_names.at[idx], parts[idx], suffixes[idx]) for idx in group.index}
            if len(rendered) == len(group):
                break  # already unique; more fields would only add noise

    return parts, suffixes


def build_variant_descriptions(result_df: pd.DataFrame) -> pd.Series:
    """
    Describe what sets each datapoint apart from its own tool's other submissions.

    This is :func:`build_workflow_labels` without the tool name: the parenthetical alone, so it
    can sit under the tool name in a hover box or in a column of its own beside it rather than
    being folded into one long string. A tool submitted once has nothing it differs from, and
    gets an empty description.

    Parameters
    ----------
    result_df : pd.DataFrame
        Datapoints to describe. Must carry ``software_name``; any of
        :data:`WORKFLOW_LABEL_FIELDS` are used when present.

    Returns
    -------
    pd.Series
        Descriptions aligned to ``result_df.index``, empty where nothing differs.
    """
    if "software_name" not in result_df.columns or len(result_df) == 0:
        return pd.Series([], dtype=str) if len(result_df) == 0 else pd.Series("", index=result_df.index)

    software_names = result_df["software_name"].astype(str)
    display_names = _display_name_series(result_df, software_names)
    parts, suffixes = _variant_fields(result_df, software_names, display_names)
    return pd.Series(
        [(", ".join(parts[idx]) + suffixes[idx]).strip() for idx in result_df.index],
        index=result_df.index,
        dtype=object,
    )


def build_display_labels(
    result_df: pd.DataFrame,
    ranks: Optional[pd.Series] = None,
    evaluation_type: str = "mass",
    ambiguity_combo: Optional[str] = None,
) -> pd.Series:
    """
    Build the label shown for each datapoint: its tool, plus its rank within that tool.

    Short, always unique, and unaffected by how many parameters differ. What a run actually was
    is said separately, by :func:`build_variant_descriptions`, rather than being folded into the
    name.

    Parameters
    ----------
    result_df : pd.DataFrame
        Datapoints to label. Must carry ``software_name``.
    ranks : pd.Series, optional
        Precomputed ranks from :func:`rank_within_tools`, reused to avoid ranking twice when
        the caller already has them. Computed here when omitted.
    evaluation_type : str
        Evaluation type used when ranks have to be computed.
    ambiguity_combo : str, optional
        Exact-mode ambiguity combination used when ranks have to be computed.

    Returns
    -------
    pd.Series
        Labels aligned to ``result_df.index``.
    """
    if len(result_df) == 0:
        return pd.Series([], dtype=str)

    if ranks is None:
        ranks, _ = rank_within_tools(result_df, evaluation_type, ambiguity_combo)
    software = (
        result_df["software_name"].astype(str)
        if "software_name" in result_df.columns
        else pd.Series("Custom", index=result_df.index)
    )
    return pd.Series(
        [f"{software.at[idx]} #{int(ranks.at[idx])}" for idx in result_df.index],
        index=result_df.index,
        dtype=object,
    )
