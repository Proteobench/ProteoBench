# Benchmark module life cycle

Anybody can propose a new benchmark module, and discuss on the validity of current modules. There are 6 phases in the benchmark modules life cycle:
1. Module proposal
2. Implementation
3. Beta 
4. Live
5. Archived
6. Withdrawn


## Proposal

Anyone can start a discussion or more formally propose new module, as described in ["How to propose/discuss a new module" section](./3-module-proposal.md).

The proposal will be public, and discussed with the community before being implemented. We are currently setting up a reviewing process through [GitHub discussions](https://github.com/orgs/Proteobench/discussions).

## Implementation

*Implementation may or may not be done by the people who made the proposal.*

Once fully reviewed and accepted, the editor moves the Proposal from Discussions to Issues. Based on this new issue (which can be labeled as “new benchmark module”), describing the finalized Proposal, the module can be implemented and documented in the ProteoBench codebase. Finally, a pull request (PR) can be opened.

After two positive code reviews by ProteoBench maintainers, the PR can be merged. The PR MUST meet the following requirements:
1. Proper documentation of the benchmarking module
2. Proper documentation of the code
3. All code should follow Black styling
4. The latest commit of the PR should pass the continuous integration tests

## Beta

When the PR is merged, the new module enters a beta stage, where its code base is part of the Python package, and it is present on the web platforms. However, a prominent banner states that the module is still in “Beta”. After a minimal period of one month and approval by the initial proposers and external reviewers, the beta label can be removed.

## Live

The benchmark module is accessible to the community without restriction.

## Archived

Benchmark modules that are still valid but superseded by a better alternative. We still display the module on the web platforms and in the stable code base, but do not accept new reference runs anymore. A banner is also displayed, stating the status.

## Withdrawn

Benchmark modules that in hindsight proved to be flawed in any way and should no longer be used in any context. Code is removed from the Python package, and the module and its results are removed from the web platforms.
