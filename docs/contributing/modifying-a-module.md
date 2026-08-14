# Modifying an existing module

We recommend keeping a module's existing structure intact.

## Adding a new tool to an existing module

To support a new data analysis tool in an existing benchmark module, you need to:

- add a `.toml` file for the tool's output parsing
- add a parameter-parsing function for the tool
- extend the module's documentation with setup instructions for the new tool

As an example, see how quantms was added to the DDA quantification precursor-ion module in
[PR #550](https://github.com/Proteobench/ProteoBench/pull/550/files).

## Adding new benchmarking metrics

Add the new metrics to the datapoint class and the plot generator for visualization. See
[Adding a module](adding-a-module.rst) for the extended documentation on datapoint and plot
configuration.

```{note}
Changing the intermediate format or the datapoint structure can affect other modules. Define them
stringently from the start rather than changing them later.
```
