# Troubleshooting

Please let us know if you have issues when using ProteoBench. You can:

- create an issue [here](https://github.com/Proteobench/ProteoBench/issues/new/choose)
- contact us by email [here](mailto:proteobench@eubic-ms.org?subject=ProteoBench_troubleshooting)

You may also find a solution to your problem(s) here:

## Stable Internet Connection

Make sure you have a stable internet connection. We rely on syncing results from GitHub, 
which can lead to connections errors, see [#259](https://github.com/Proteobench/ProteoBench/issues/259).

## File format errors

If your upload fails with a parsing error, check the following:

- **Correct file selected**: Make sure you upload the correct output file for your tool (e.g. `report.tsv` for DIA-NN, not the log file in the quantification field).
- **File not renamed**: Raw files must keep their original names. Renaming files will cause column mapping failures.
- **Correct separator**: Custom format files must be tab-delimited, not comma-separated.
- **Missing columns**: Ensure all required columns are present in your output file. Check the module-specific documentation for the exact column requirements.

## Parameter file issues

- **Wrong parameter file**: Each tool requires a specific parameter/configuration file. For example, DIA-NN requires the `*.log.txt` file, MaxQuant requires `mqpar.xml`, FragPipe requires `fragpipe.workflow`.
- **Parameters not parsed**: If parameters appear as empty or "Not specified" after upload, the parameter file may be from an unsupported version of the tool. Please open a [GitHub issue](https://github.com/Proteobench/ProteoBench/issues/new/choose) with your parameter file attached.

## Species annotation

Protein identifiers in your results must contain species flags to allow ProteoBench to assign proteins to the correct species. The expected flags depend on the module:

- **HYE modules** (most quantification modules): `_HUMAN`, `_YEAST`, `_ECOLI`
- **HY modules** (single cell): `_HUMAN`, `_YEAST`

If species cannot be determined, precursor ions will be excluded from metric calculation. Use the provided FASTA files to ensure correct annotation.

## Contaminant handling

Contaminant proteins must be prefixed with `Cont_` in the FASTA file. ProteoBench automatically removes contaminant sequences during metric calculation. If you use a different contaminant prefix, the contaminants will not be filtered and may affect your results.

## Tool version compatibility

Some tools require a minimum version for correct parsing:

- **AlphaDIA**: Version >= 1.10.4 is recommended for optimal performance and correct parameter parsing.
- **AlphaPept**: Considered a legacy tool (not actively developed).

---

> **DOCUMENTATION GAPS**
>
> This section could be expanded with common issues encountered by users:
>
> - **File format errors**: Common parsing failures when uploading results (wrong separator, missing columns, wrong file selected)
> - **Parameter file issues**: What happens when the wrong parameter file is uploaded, or when parameters cannot be parsed
> - **Species annotation errors**: Issues with protein identifiers not containing species flags (e.g. `_HUMAN`, `_YEAST`)
> - **Contaminant prefix**: Clarification that contaminants must be prefixed with `Cont_` in the FASTA
> - **File renaming**: Reminder that raw files must not be renamed (referenced in module docs but not in troubleshooting)
> - **Browser compatibility**: Any known issues with specific browsers
> - **Large file uploads**: Timeout or size limit issues when uploading large result files
> - **Version-specific issues**: Known incompatibilities with specific tool versions (e.g. AlphaDIA version requirements)
