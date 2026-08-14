# Your first submission

The most common way to contribute to ProteoBench is to submit the results of running your own
workflow on a benchmark dataset. This page walks through that process end to end, in detail.

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
required to match them exactly.

```{admonition} Automate this step with ProteoRunners
:class: tip
[ProteoRunners](https://github.com/Proteobench/ProteoRunners) is a Nextflow pipeline that runs
several search engines (DIA-NN, AlphaDIA, Sage, FragPipe, MaxQuant, MetaMorpheus) on ProteoBench
benchmark datasets inside Docker containers, so no manual tool installation is needed. It is
useful if you want to benchmark multiple tools at once or reproduce a baseline run. Start it with:
`nextflow run ProteoBench/ProteoRunners -r v1.0.0`. The pipeline's outputs are already structured
for direct upload in step 4 below.
```

## 4. Upload and inspect your results privately

Open the module's web app page and use the "Upload New Results" tab. Upload the specific output
file(s) indicated in the submission box. The output files are also listed on the module's page (see its "Tool-specific setup" section for the exact filename and
any tool-specific settings). ProteoBench runs its scoring pipeline immediately and shows you
interactive plots and tables comparing your run against the public results — nothing is shared yet
at this point.

### If your tool isn't supported

If there's no parser for your tool yet, upload results in the **custom tabular format** instead. It
is a tab-delimited table with the minimum information necessary to calculate the module metrics. Columns are described in the respective module documentation page.

Results submitted in the custom format can be inspected privately but currently can't be made
public — see [Contributing](../contributing/index.md) or
[open an issue](https://github.com/Proteobench/ProteoBench/issues) if you'd like native support for
your tool added instead.

## 5. Fill in the metadata

To publicly submit your workflow run, go to the tab "Submit New Results". In the `Meta data for searches` field, upload the parameter file your search tool produced (again,
see the module page's "Tool-specific setup" for which file). ProteoBench parses what it can
automatically; add anything it couldn't extract — or anything you think is important context — in
the `Comments for submission` field. In case you did any post-processing such as filtering, tick `Was any postprocessing applied?`, and describe the steps in the field below.

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

Confirm the metadata is correct, then press **"I really want to upload it"**. ProteoBench will run a couple of automatic validation steps, which might throw warnings. 
After a brief moment and a couple of celebratory balloons, you will see a link to the Pull request opened with your submission — save it. That link contains your submission's unique
identifier, lets you track its status, and lets you leave comments for the ProteoBench maintainers.

**What a reviewer checks**, so you know what to expect:

1. Any validation warnings or notes you left in the comments field.
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
