# About

## What is ProteoBench?

[ProteoBench](https://proteobench.cubimed.rub.de/) is an open, community-curated platform for
benchmarking proteomics data analysis workflows. It lets anyone compare how different tools,
versions, and parameter choices perform on the same standardized datasets — continuously, and
without needing to run every tool yourself.

You download a set of input files for a data type you care about, analyze them with your own
workflow, and upload the results. ProteoBench then computes a standard set of metrics from your
output and shows them alongside every other public result for that same benchmark, so differences
in performance reflect differences in workflows, not differences in data.

```{button-ref} /modules/index
:color: primary
:class: sd-mr-2

Browse the benchmarking modules
```
```{button-ref} /your-first-submission/index
:color: secondary
:outline:

Submit your first result
```

## Who is it for?

- **End-users** — researchers and core facilities who want to pick a workflow that fits their data,
  or check how their routine analysis compares to the state of the art.
- **Developers** — people building or maintaining analysis software who want to see exactly where
  their tool is strong or weak, and track that over versions.
- **The wider community** — anyone who wants to see how a newly published workflow stacks up
  against existing ones, with the full parameters behind every result available to inspect.

## What ProteoBench is — and isn't

ProteoBench:

- Makes it easy to compare existing data analysis workflows, in a controlled way
- Gives newly developed workflows a frame of reference
- Documents benchmarks that each highlight specific strengths or weaknesses of a workflow (or a
  step within it)
- Grows continuously as the community adds new modules, datasets, and use cases

ProteoBench deliberately **does not**:

- Point to a single "best" workflow for every use case
- Provide evidence for sweeping claims about a workflow's general performance
- Serve as the sole performance measure for a tool under active development

A tool that performs well on one module, dataset, or metric may not be the best choice for a
different instrument, acquisition method, or biological question. Treat ProteoBench as
transparent, reproducible decision support — not a leaderboard.

## Need more help?

See [Contact](../contact.md) for all the ways to reach us.
