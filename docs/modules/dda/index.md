# DDA modules

Modules for data acquired with data-dependent acquisition (DDA).

::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} LFQ, precursor ion (QExactive)
:link: dda-ion-qexactive
:link-type: doc

{bdg-info}`beta` {bdg-primary-line}`Quantification`

Quantification accuracy and sensitivity on a Q Exactive HF-X Orbitrap. The reference module to
start with if you're new to ProteoBench.
:::

:::{grid-item-card} LFQ, peptidoform (QExactive)
:link: dda-peptidoform
:link-type: doc

{bdg-info}`beta` {bdg-primary-line}`Quantification`

Same dataset and metrics as the ion-level module, but scored at the peptidoform level.
:::

:::{grid-item-card} LFQ, precursor ion (Astral)
:link: dda-ion-astral
:link-type: doc

{bdg-info}`beta` {bdg-primary-line}`Quantification`

Quantification accuracy and sensitivity for DDA data acquired on an Orbitrap Astral.
:::

:::{grid-item-card} De novo sequencing (DDA-HCD)
:link: denovo-dda-hcd
:link-type: doc

{bdg-success}`alpha` {bdg-primary-line}`Identification`

Peptide sequencing accuracy for *de novo* models and algorithms on HCD-fragmented DDA data.
:::

::::

See [Modules](../index.rst) for what a module documentation page covers, or jump to
[DIA modules](../dia/index.md) instead.

```{toctree}
:hidden:

dda-ion-qexactive
dda-peptidoform
dda-ion-astral
denovo-dda-hcd
```
