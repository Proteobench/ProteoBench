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

:::{grid-item-card} LFQ, precursor ion (Astral, low input)
:link: dia-ion-astral-lowinput
:link-type: doc

{bdg-success}`alpha` {bdg-primary-line}`Quantification`

Quantification accuracy and sensitivity for a 200 pg low-input DIA dataset on an Orbitrap Astral.
:::

:::{grid-item-card} LFQ, precursor ion (timsTOF, low input)
:link: dia-ion-timstof-lowinput
:link-type: doc

{bdg-success}`alpha` {bdg-primary-line}`Quantification`

Quantification accuracy and sensitivity for a 200 pg low-input dia-PASEF dataset on a timsTOF Ultra 2.
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

::::

See [Modules](../index.rst) for what a module documentation page covers, jump to
[DDA modules](../dda/index.md), or see [Archived modules](../archived/index.md) for modules that
have been superseded (LFQ precursor ion AIF, LFQ low input).

```{toctree}
:hidden:

dia-ion-diapasef
dia-ion-astral
dia-ion-zenotof
dia-ion-astral-lowinput
dia-ion-timstof-lowinput
dia-ion-plasma
entrapment-dia-astral
```
