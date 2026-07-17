# Your first submission

The most common way to contribute to ProteoBench is to submit the results of running your own
workflow on a benchmark dataset. This page walks through that process end to end, once, in detail —
every module page links back here instead of repeating it.

```{admonition} Looking to contribute code instead?
:class: tip
If you want to add a module, fix a bug, or improve the codebase, see
[Contributing](../contributing/index.md) instead. This page is about submitting a **benchmark run**,
which needs no coding at all.
```

## 1. Pick a module

Open the [Modules](../modules/index.rst) page and choose the one that matches your data type and
question — for example, a DDA or DIA quantification module for a given instrument, or the de novo
sequencing or FDR-validation modules. Each module page states exactly what it tests and what it
doesn't.

## 2. Download the input data

Every module page links to its raw MS files (and a matching FASTA, where relevant) from the
ProteoBench data server, and usually from a public repository such as ProteomeXchange as an
alternative. Also grab the download from the "Download raw files" button on the module's web app
page if you prefer.

```{important}
**Do not rename the downloaded files.** ProteoBench matches raw file names to conditions and
replicates; renamed files will fail to parse correctly.
```

## 3. Run your workflow

Analyze the downloaded files with your own tool, using whatever parameters you'd like to test. Most
modules suggest a starting set of parameters for a fair baseline comparison, but you are not
required to match them exactly (see the [FAQ](../about/faq.md#do-i-need-to-use-the-same-workflow-parameters-as-other-users)).

## 4. Upload and inspect your results privately

Open the module's web app page and use the "Upload New Results" tab. Upload the specific output
file(s) that module's page lists (see its "Tool-specific setup" section for the exact filename and
any tool-specific settings). ProteoBench runs its scoring pipeline immediately and shows you
interactive plots and tables comparing your run against the public results — nothing is shared yet
at this point.

### If your tool isn't supported

If there's no parser for your tool yet, upload results in the **custom tabular format** instead. It
is a tab-delimited table with one row per quantified precursor and these columns (exact names/casing
vary slightly by module — check that module's Custom format section):

- `Sequence` — peptide sequence without modifications
- `Modified sequence` — sequence with localized modifications, ideally in
  [ProForma](https://www.psidev.info/proforma) notation
- `Proteins` — protein identifiers, `;`-separated, including the species flag (e.g. `_YEAST`)
- `Charge` — precursor charge state
- one quantitative column per raw file/sample

Results submitted in the custom format can be inspected privately but currently can't be made
public — see [Contributing](../contributing/index.md) or
[open an issue](https://github.com/Proteobench/ProteoBench/issues) if you'd like native support for
your tool added instead.

## 5. Fill in the metadata

In the `Meta data for searches` field, upload the parameter file your search tool produced (again,
see the module page's "Tool-specific setup" for which file). ProteoBench parses what it can
automatically; add anything it couldn't extract — or anything you think is important context — in
the `Comments for submission` field.

Every module tracks roughly the same core parameters: software name and version, search engine
(if different), FDR thresholds, enzyme and missed cleavages, peptide length and charge range,
fixed/variable modifications, and match-between-runs. Check the module page's "Parameters" section
for the complete list for that module.

```{admonition} Check your parameter file for personal information
:class: warning
Parameter files can embed local file paths — FASTA location, raw data location, tool installation
paths — that may reveal a personal username or institutional directory structure. Review and
sanitize paths before submitting.
```

## 6. Submit for public review

Confirm the metadata is correct, then press **"I really want to upload it"**. This opens a pull
request on GitHub and gives you a link — save it. That link contains your submission's unique
identifier, lets you track its status, and lets you leave comments for the ProteoBench maintainers.

**What a reviewer checks**, so you know what to expect:

1. Any warnings or notes you left in the comments field.
2. Whether parameter values that were filled in manually (not detected in your parameter file)
   make sense, and whether any detected values were justified if changed.
3. Whether the parsed parameter values look reasonable overall.
4. That your submitted data is actually present on the server — for example, a submission made
   from a local install without the data being uploaded won't be accepted.

This usually takes a few working days. If something needs fixing, the reviewer will comment on your
PR.

## 7. Your run goes public

Once merged, your workflow's output, parameters, and metrics are stored publicly and plotted
alongside every other validated run for that module — visible to the whole community, and staying
that way as new submissions arrive.

## Questions?

[Open an issue](https://github.com/Proteobench/ProteoBench/issues/new) or
[email us](mailto:proteobench@eubic-ms.org?subject=ProteoBench_query).
