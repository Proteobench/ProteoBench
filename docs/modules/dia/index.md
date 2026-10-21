# DIA modules

Modules for data acquired with data-independent acquisition (DIA).

::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} LFQ, precursor ion (diaPASEF)
:link: dia-ion-diapasef
:link-type: doc

{bdg-info}`beta` {bdg-primary-line}`Quantification`

Quantification accuracy and sensitivity for diaPASEF data on a timsTOF SCP.
:::

:::{grid-item-card} LFQ, precursor ion (Astral)
:link: dia-ion-astral
:link-type: doc

{bdg-info}`beta` {bdg-primary-line}`Quantification`

Quantification accuracy and sensitivity for DIA data acquired on an Orbitrap Astral.
:::

:::{grid-item-card} LFQ, precursor ion (ZenoTOF)
:link: dia-ion-zenotof
:link-type: doc

{bdg-info}`beta` {bdg-primary-line}`Quantification`

Quantification accuracy and sensitivity for ZenoTOF 8600 ZenoSWATH data.
:::

:::{grid-item-card} LFQ, low input
:link: dia-ion-lowinput
:link-type: doc

{bdg-success}`alpha` {bdg-primary-line}`Quantification`

Quantification accuracy and sensitivity for low-input / single-cell-scale DIA on an Astral.
:::

:::{grid-item-card} LFQ, human plasma
:link: dia-ion-plasma
:link-type: doc

{bdg-success}`alpha` {bdg-primary-line}`Quantification`

Quantification accuracy and dynamic range for human plasma DIA data.
:::

:::{grid-item-card} DIA Ion Entrapment (Astral)
:link: entrapment-dia-astral
:link-type: doc

{bdg-success}`alpha` {bdg-primary-line}`FDR validation`

Checks whether a DIA search engine's reported FDR is reliable, using entrapment peptides.
:::

:::{grid-item-card} LFQ, precursor ion (AIF)
:link: dia-ion-aif
:link-type: doc

{bdg-dark}`archived` {bdg-primary-line}`Quantification`

Superseded by the diaPASEF/Astral/ZenoTOF modules above; kept for reference.
:::

::::

See [Modules](../index.rst) for what a module documentation page covers, or jump to
[DDA modules](../dda/index.md) instead.

```{toctree}
:hidden:

dia-ion-diapasef
dia-ion-astral
dia-ion-zenotof
dia-ion-lowinput
dia-ion-plasma
entrapment-dia-astral
dia-ion-aif
```
