.. _submission-validation:

######################
Submission validation
######################

ProteoBench validates an uploaded submission before the public datapoint is
created. The validation layer checks that the standardized results and the
parsed parameters are internally consistent and consistent with the module
reference database, and returns a structured ``ValidationReport``.

Validation is **non-blocking**. Every finding, including ``error``-severity
ones, is shown to the submitter and embedded in the pull-request description for
the reviewers, but submission always proceeds. Severity controls only display
prominence and inclusion in the pull-request summary. It does not gate the
submission flow.

The layer is framework-agnostic and **registry-driven**. Each module maps to a
*validation profile* (a named, ordered set of checks). Adding a new module of an
existing category is configuration-only. Adding a genuinely new category only
requires registering a new profile. The orchestrator never needs to change.

The code lives in the ``proteobench.validation`` package. The Streamlit glue
lives in :file:`webinterface/pages/base_pages/utils/validation_ui.py`.


Package layout
==============

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - File
     - Contents
   * - ``report.py``
     - ``Severity`` enum (``error`` / ``warning`` / ``info``), ``ValidationIssue``,
       and ``ValidationReport`` (issue collection plus ``has_errors``, ``passed``,
       ``summary()``, ``raise_if_errors()``).
   * - ``context.py``
     - ``ValidationContext``: bundles everything a check might need
       (``standard_df``, ``parameters``, ``config``, ``fasta``, ``input_format``,
       a generic ``reference``, and an ``extras`` dict) so every check has the
       uniform signature ``ctx -> list[ValidationIssue]``.
   * - ``config.py``
     - ``ModuleValidationConfig``: column names, contaminant flag, decoy
       prefixes, reference FASTA location, and the resolved
       ``validation_profile``. Built with ``from_parse_settings(...)``.
   * - ``checks.py``
     - Pure, individually testable check functions (protein IDs, charge range,
       peptide length, enzyme, modifications, maximum modifications, mass
       tolerances, PSM FDR, run consistency).
   * - ``profiles.py``
     - ``Check``, ``ValidationProfile``, the profile **registry**
       (``register_profile`` / ``unregister_profile`` / ``get_profile`` /
       ``available_profiles``), and the built-in ``quant_lfq`` and ``denovo``
       profiles. This is the extensibility surface.
   * - ``validator.py``
     - ``validate_submission(...)``: resolves the profile, builds the context,
       runs the profile's checks, and returns the report. Each check is
       fault-tolerant: an unexpected exception becomes a warning.
   * - ``fasta.py``
     - ``FastaReference``: builds the expected protein set from FASTA text, a
       path, bytes, a zip / gzip, or a URL.
   * - ``protein_ids.py``
     - Helpers to split protein groups, extract identifiers, and skip decoys and
       contaminants.
   * - ``exceptions.py``
     - ``SubmissionValidationError``, which wraps a report for programmatic
       callers that opt in to raising.


Data flow
=========

.. code-block:: text

   module_settings.toml + parser  --> ModuleValidationConfig.from_parse_settings(...)
   reference FASTA                --> FastaReference.from_url(...)
                                         |
   standardized DataFrame + params -----+--> validate_submission(...)
                                         |        |
                                         |        +-- resolve profile (registry)
                                         |        +-- build ValidationContext
                                         |        +-- run each Check (fault-tolerant)
                                         v
                                    ValidationReport  --> UI display + PR summary

The core validator performs no I/O. Any reference data (a FASTA, a ground-truth
table) is supplied through the arguments. The front end is responsible for
obtaining the standardized DataFrame and the reference, which is what the
Streamlit glue does.


Built-in profiles
==================

``quant_lfq``
   Runs, in order: ``protein_ids`` (against the reference FASTA),
   ``charge_range``, ``peptide_length``, ``enzyme``, ``modifications``,
   ``max_modifications``, ``mass_tolerances``, ``fdr_psm``, and
   ``run_consistency``. ``protein_ids``, ``charge_range``, and ``peptide_length``
   default to ``error`` severity; the rest default to ``warning``.

``denovo``
   Runs ``run_consistency`` plus a ``denovo_pending`` informational placeholder.
   De novo uses a different standardized schema and a ground-truth table rather
   than a FASTA, so content checks are a documented to-do in ``profiles.py``.

Checks are reusable across profiles. For example, ``run_consistency`` is shared
by both built-in profiles.


Integrating validation for a new module
========================================

Existing category (quantification)
-----------------------------------

For a quantification module no code is required. Two configuration steps are
enough:

1. Add a reference database to the module's ``module_settings.toml`` (beside
   ``[species_expected_ratio]`` and ``[general]``):

   .. code-block:: toml

      [reference_database]
      "fasta_url" = "https://proteobench.cubimed.rub.de/fasta/ProteoBenchFASTA_MixedSpecies_HYE.zip"
      # "fasta_filename" = "optional_member_name_inside_the_archive.fasta"

   If ``[reference_database]`` is absent, the protein-identifier check is skipped
   with an informational message and the other checks still run.

2. The profile resolves automatically to ``quant_lfq`` from the module's parser
   class (``IntermediateFormatConverter``), so no profile declaration is needed. You may
   pin it explicitly if you prefer:

   .. code-block:: toml

      [validation]
      "profile" = "quant_lfq"

The orchestrator and the submission tab already run the resolved profile. The
profile is resolved by ``ModuleValidationConfig.from_parse_settings`` in this
order of precedence:

1. an explicit ``[validation].profile`` key in ``module_settings.toml``;
2. inference from the parser class via the ``MODULE_TO_CLASS`` registry
   (``IntermediateFormatConverter`` -> ``quant_lfq``, ``ParseSettingsDeNovo`` -> ``denovo``);
3. the ``DEFAULT_VALIDATION_PROFILE`` fallback (``quant_lfq``).

An unregistered profile name produces a single ``unknown_validation_profile``
warning and runs nothing. It never blocks.

New category
------------

A genuinely new category of module needs a profile of its own:

1. Write the checks it needs (see below), or reuse existing ones.
2. Register a ``ValidationProfile`` in ``profiles.py`` (or, from third-party
   code, via ``register_profile``).
3. Point the module at it with ``[validation] profile = "<name>"`` in
   ``module_settings.toml``. If you want the profile to be inferred from the
   parser class instead, add an entry to ``_PROFILE_BY_PARSER_CLASS`` in
   ``config.py``.

The orchestrator (``validate_submission``) is generic and does not change.


Extending and maintaining the checks
=====================================

Adding a check
--------------

A check is a pure function with the signature ``ctx -> list[ValidationIssue]``.
Add it to :file:`proteobench/validation/checks.py`, keeping it independently
unit-testable, then register it in the relevant profile in ``profiles.py``.

.. code-block:: python

   # proteobench/validation/checks.py
   from proteobench.validation.context import ValidationContext
   from proteobench.validation.report import ValidationReport, ValidationIssue
   from typing import List


   def check_my_constraint(standard_df, parameters, config) -> List[ValidationIssue]:
       """Check some property of the standardized results against a parameter."""
       report = ValidationReport()

       # Parameter-dependent checks must self-report when the value was not
       # parsed, and never crash.
       limit = getattr(parameters, "my_limit", None)
       if limit is None:
           report.add_warning(
               "my_limit_absent",
               "The parameter 'my_limit' could not be parsed; the check was skipped.",
               "my_constraint",
           )
           return report.issues

       offending = standard_df[standard_df["some_column"] > limit]
       if not offending.empty:
           report.add_error(
               "my_constraint_violated",
               f"{len(offending)} row(s) exceed my_limit ({limit}).",
               "my_constraint",
               observed=int(offending["some_column"].max()),
               expected=f"<= {limit}",
               examples=offending["some_column"].head(10).tolist(),
           )
       return report.issues

Then add it to a profile. Trivial checks that only forward context fields are
written as a lambda adapter; checks that need orchestration logic (such as
deciding whether a reference is available) are written as named functions in
``profiles.py``.

.. code-block:: python

   # proteobench/validation/profiles.py
   QUANT_LFQ_PROFILE = ValidationProfile(
       name="quant_lfq",
       checks=[
           # ... existing checks ...
           Check(
               "my_constraint",
               lambda ctx: check_my_constraint(ctx.standard_df, ctx.parameters, ctx.config),
               "What this check verifies.",
           ),
       ],
   )

Guidelines for checks:

- Use ``ValidationContext`` fields: ``ctx.standard_df``, ``ctx.parameters``,
  ``ctx.config``, ``ctx.fasta``, ``ctx.input_format``.
- Choose severity by intent only. ``error`` and ``warning`` differ in display
  prominence and pull-request inclusion. Neither blocks submission.
- A parameter-dependent check should emit a ``warning`` when the constraint was
  not parsed, rather than failing. The orchestrator also wraps every check so an
  unexpected exception becomes a ``check_failed`` warning, but checks should not
  rely on that.

Registering a profile
----------------------

.. code-block:: python

   from proteobench.validation import Check, ValidationProfile, register_profile

   register_profile(
       ValidationProfile(
           name="my_module",
           description="Checks for the new module category.",
           checks=[Check("my_check", my_check_func, "what it does")],
       )
   )

The registry helpers are ``register_profile`` (with ``overwrite=False`` by
default), ``unregister_profile``, ``get_profile``, and ``available_profiles``.

The report object
------------------

``validate_submission`` returns a ``ValidationReport``. Useful members:

- ``report.errors`` / ``report.warnings`` / ``report.infos``: issues by severity.
- ``report.has_errors`` and ``report.passed``: informational only. The Streamlit
  flow does not gate on them.
- ``report.summary()``: a compact Markdown summary embedded in the pull-request
  description.
- ``report.raise_if_errors()``: optional path for programmatic callers that
  prefer an exception (``SubmissionValidationError``).

Each ``ValidationIssue`` carries a machine-readable ``code``, a ``severity``, a
human-readable ``message``, the originating ``check`` name, and optional
``field``, ``observed``, ``expected``, and ``examples`` values.


Web integration
================

Validation runs inside ``submit_to_repository`` in
:file:`webinterface/pages/base_pages/tabs/tab6_submit_results.py`, after the
confirmation button and before the pull request is created. The standardized
DataFrame is re-derived by rerunning the existing parser on the input DataFrame
already in session state, so no tool-specific parsing logic is duplicated. The
glue functions are in
:file:`webinterface/pages/base_pages/utils/validation_ui.py`:

- ``run_submission_validation(variables, ionmodule, user_input, params)`` runs
  the full flow (re-parse, load and cache the FASTA, run the checks) and returns
  a ``ValidationReport``. It is fault-tolerant: any infrastructure problem
  (missing input, parser failure, FASTA download failure) becomes a warning.
- ``render_validation_report(report)`` displays errors and warnings, with info
  items inside a collapsed expander.

The findings are rendered in the UI and appended to the pull-request description
through ``report.summary()``. None of them block the pull request. The local
Tab 2 upload path is unaffected.


Testing
=======

Validation is covered by :file:`test/test_validation.py`, which tests FASTA
parsing, protein-identifier matching, the individual checks, the profile
registry (resolution, custom-profile registration, unknown-profile handling, de
novo routing), report serialization, and integration through the real MaxQuant
and Sage parsers. A small reference FASTA fixture lives at
:file:`test/data/validation/ProteoBench_validation_reference.fasta`.

When you add a check, add unit tests for it directly (it is a pure function).
When you add a profile, add a test that the profile resolves for the module and
that its checks run.


Documented limitations
=======================

Some checks are intentionally limited because the required reference data is not
available:

- Full enzyme-specificity checks need reference protein sequences. Only internal
  K/R counting is done for the trypsin family, as a heuristic.
- Cross-tool modification normalization is not implemented. Tools encode
  modifications differently (human-readable names, UniMod accessions, raw mass
  dictionaries); only matching human-readable names against the declared
  modifications is attempted.
- Run-level matching (raw file, sample, experiment) is not possible because
  ``ProteoBenchParameters`` does not expose those fields. Only software identity
  is compared in ``run_consistency``.
