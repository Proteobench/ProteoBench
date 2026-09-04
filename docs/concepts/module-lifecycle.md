# Benchmark module lifecycle

Anyone can propose a new benchmark module or discuss the validity of an existing one. A module
moves through six phases:

1. Proposal
2. Alpha (late implementation phase)
3. Beta
4. Live
5. Archived
6. Withdrawn

## Proposal

Anyone can start a discussion or formally propose a new module, as described in
[Propose a module](../contributing/propose-a-module.md). The proposal is public and discussed with
the community during development, and requires input from at least one external expert.
**Modules that were not openly discussed with the community and an expert carry a cautionary
"Alpha" banner on their page.**

## Implementation

Implementation may or may not be done by the people who made the proposal; see
[Propose a module](../contributing/propose-a-module.md) for the development process.

## Alpha

Once the implementing PR is merged, the module enters Alpha: its code is part of the Python
package and it's live on the web platform, but a prominent banner states it's still in Alpha
because it remains to be fully discussed with experts.

## Beta

The initial proposer(s) and external expert(s) must approve the module before "Alpha" becomes
"Beta". At this stage workflow results may still change (new tools being added, parsing fixes, or
simply because the module is very new). The proposer(s) can remove the "Beta" banner after a
minimum of six months.

## Live

The module is accessible to the community without restriction.

## Archived

The module is still valid but superseded by a better alternative. It stays visible on the web
platform and in the stable codebase, but no longer accepts new reference runs. A banner states its
archived status.

## Withdrawn

The module proved flawed in some way and should no longer be used in any context. Its code is
removed from the Python package, and the module and its results are removed from the web platform.
