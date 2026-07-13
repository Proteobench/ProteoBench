This module uses entrapment peptides to test whether DIA workflows control false discovery rate (FDR) at the global precursor ion level.

The benchmark uses three technical replicates of a human plasma digest acquired on an Orbitrap Astral in DIA mode with a 15-minute gradient. The search database is a pre-digested ProteoBench entrapment FASTA containing human peptides, contaminants, and matched entrapment peptides that cannot be present in the sample.

ProteoBench classifies each identified precursor as target or entrapment, maps entrapment peptides to their paired target peptides, and reports lower-bound, combined, and paired false discovery proportion (FDP) estimates. These estimates are compared with the FDR threshold parsed from the submitted tool output.

The module accepts DIA-NN, FragPipe, FragPipe (DIA-NN quant), and AlphaDIA outputs. For a valid comparison, keep the raw file names unchanged, use the ProteoBench entrapment FASTA, disable in-silico digestion, and do not add variable modifications.
