# Benchmark module life cycle

Anybody can propose a new benchmark module, and discuss on the validity of current modules. There are 6 phases in the benchmark modules life cycle:

1. Module proposal
2. Alpha (late phase of implementation)
3. Beta 
4. Live
5. Archived
6. Withdrawn


## Proposal

Anyone can start a discussion or more formally propose new module, as described in ["How to propose/discuss a new module" section](./3-module-proposal.md).

The proposal will be public, and discussed with the community before being implemented and during development. Additionally, we require input from external expert(s). **Modules that were not openly discussed with the community and expert(s) are highlighted with a cautionary message on the top of their page ("Alpha" banner)**.

## Implementation

*Implementation may or may not be done by the people who made the proposal.*
See the page ["How to propose/discuss a new module" section](./3-module-proposal.md) for more detailed information on the development process.

## Alpha

When the PR is merged, the new module enters a "Alpha" stage, where its code base is part of the Python package, and it is present on the web platforms. However, a prominent banner states that the module is still in "Alpha". After approval by the initial proposer(s) and external expert(s), the alpha label can be removed.

## Alpha

When the PR is merged, the new module enters an alpha stage, where its code base is part of the Python package, and it is present on the web platforms. However, a prominent banner states that the module is still in "Alpha". This means that the module is available but remains to be fully discussed with experts (more information on module proposal process can be found [here](./3-module-proposal.md)). 

## Beta

The module should be approved by the initial proposer(s) and external expert(s) before the banner "Alpha" can be changed to "Beta". At this stage, workflow results may still change. This can happen if we expect new tools to be included (and potential parsing mistakes), or if the module is very new. The "Beta" banner can be removed by the initial proposer(s) of the module after a minimum of six months.

## Live

The benchmark module is accessible to the community without restriction.

## Archived

Benchmark modules that are still valid but superseded by a better alternative. We still display the module on the web platforms and in the stable code base, but do not accept new reference runs anymore. A banner is also displayed, stating the status.

## Withdrawn

Benchmark modules that in hindsight proved to be flawed in any way and should no longer be used in any context. Code is removed from the Python package, and the module and its results are removed from the web platforms.
