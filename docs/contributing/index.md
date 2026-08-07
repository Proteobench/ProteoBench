# Contributing

This section is about contributing to the ProteoBench **codebase**: fixing bugs, adding a module,
or proposing changes. If you're looking to submit a **benchmark run** instead, see
[Your First Submission](../your-first-submission/index.md) — no coding required for that.

```{toctree}
:hidden:

propose-a-module
development-setup
local-usage
adding-a-module
modifying-a-module
parameter-homogenization
repo-layout
submission-validation
reviewing-a-submission
contributors
changelog
```

```{toctree}
:caption: Python API
:glob:
:maxdepth: 3
:hidden:

api/proteobench/proteobench
api/webinterface/webinterface
```

## Before you begin

If you have an idea for a feature, a use case to add, or an approach for a bug fix, communicate it
with the community first by opening a thread in
[GitHub Discussions](https://github.com/proteobench/proteobench/discussions) or
[GitHub Issues](https://github.com/proteobench/proteobench/issues).

Not sure where to start? Check the
[open issues](https://github.com/proteobench/proteobench/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22+label%3A%22help+wanted%22)
labeled `good first issue` or `help wanted`. If you want to add a new benchmark module, start with
[Propose a module](propose-a-module.md) rather than opening a PR directly.

## Setting up your environment

See [Development setup](development-setup.md) for installing the package, running tests, and
building the documentation locally.

## How to contribute code

1. Fork [ProteoBench](https://github.com/proteobench/proteobench) on GitHub.
2. Commit and push your changes to your
   [fork](https://help.github.com/articles/pushing-to-a-remote/).
3. Ensure tests and documentation (both Python docstrings and files under `docs/`) are updated for
   your changes. Docstrings follow the
   [numpydoc style](https://numpydoc.readthedocs.io/en/latest/format.html).
4. Open a [pull request](https://help.github.com/articles/creating-a-pull-request/). Ideally
   include: why the change is needed, how it's implemented, and how to test it.
5. Make sure the PR passes the continuous integration checks run by
   [GitHub Actions](https://github.com/proteobench/proteobench/actions).

Where to go next depends on what you're changing:

- Adding a brand-new benchmark module → [Propose a module](propose-a-module.md), then
  [Adding a module](adding-a-module)
- Extending an existing module (new tool, new metric) → [Modifying a module](modifying-a-module.md)
- Adding a parameter parser for a new tool →
  [Parameter homogenization](parameter-homogenization.md)
- Understanding where things live → [Repository layout](repo-layout.md)
- Understanding submission checks → {doc}`Submission validation <submission-validation>`
- Reviewing someone else's benchmark-run PR → {doc}`Reviewing a submission <reviewing-a-submission>`

## Release workflow

When a new version is ready to be published:

1. Update the changelog (if not already done) — see {doc}`Changelog <changelog>`.
2. Merge all final changes to `main`.
3. Create a new release on GitHub.

The version itself is derived automatically from the git tag (via `setuptools_scm`) — there's no
version string to bump by hand. Publishing a GitHub release triggers the `Publish` GitHub Action,
which builds the package and publishes it to PyPI; the Bioconda automation then updates the
Bioconda package (the conda recipe needs a manual update if dependencies changed).

## Contributors

See the full list of people who contributed to ProteoBench on the {doc}`Contributors <contributors>`
page.
