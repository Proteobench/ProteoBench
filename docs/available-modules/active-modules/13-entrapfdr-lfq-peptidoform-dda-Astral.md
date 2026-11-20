# DDA identification - peptidoform level (Human lysate / Astral)

_This module is in development_

This module estimates the percentage of false identifications in the results of the analsis of data acquired with data-dependent acquisition (DDA) on an Orbitrap Astral (Thermo Fisher).

## Data set

For this module, we provide the raw files corresponding to the data dependent acquisition (DDA) analysis of a human lysate on an Astral (Thermo Fisher). Please refer to the original publication for more details [Van Puyvelde et al., 2026](https://www.biorxiv.org/content/10.64898/2026.01.29.702266v1.full.pdf)]. We use the single proteomes files, 15 min, 50 ng. Here is a more detailed description adapted from the original paper: 
A Thermo Orbitrap Astral (Thermo Fisher Scientific, Waltham, Massachusetts, United States) was coupled to a Vanquish Neo LC instrument (Thermo Fisher Scientific). Peptides were loaded directly onto the analytical column and were separated by reversed-phase chromatography using a 50 cm μPAC™ column (Thermo Fischer Scientific), featuring a structured pillar array bed with a 180 μm bed width. Buffer A consisted of 0.1% FA in water, while Buffer B contained 0.1% FA in 80% acetonitrile. Chromatographic gradient was initiated at 96% buffer A and 4% buffer B at a flow rate of 750 nL/min during 1 minute. The flow rate was then reduced to 250 nL/min, and the percentage of buffer B was further increased to 40% over 15 minutes. The mass spectrometer was operated in positive ionization mode with data-dependent acquisition, with a full MS scans over a mass range of m/z 380-980 with detection in the Orbitrap at a resolution of 180,000 and a fixed cycle time of 0.5 s. Precursor ion selection width was kept at 2-Th and a normalized collision energy of 30% was used for higher-energy collisional dissociation (HCD) fragmentation. MS scan range was set from 145 to 1450 m/z with detection in the Astral and maximum fill time of 2.5 ms. Dynamic exclusion was enabled and set to 10 s

You can download the raw files from the ProteoBench server here: TOADD
And find them in the PRIDE repository TOADD.

**It is imperative not to rename the files once downloaded!**

For this module, we built a fasta file with the UniProt Human proteome (version 2026_01) including isoforms. It contails 105,657 entries (without contaminants and decoys). We added **contaminant proteins** from
([Frankenfield et al., JPR](https://pubs.acs.org/doi/10.1021/acs.jproteome.2c00145)), and entrapment sequences generated with [FDRBench](https://github.com/Noble-Lab/FDRBench) (see [Wen, B., Freestone, J., Riffle, M. et al., 2025](https://doi-org.insb.bib.cnrs.fr/10.1038/s41592-025-02719-x) for more details on its generation). In this fasta file, the isoleucines are replaced by leucines since they are indistinguishable in these data. All protein N-terminal residues are kept in the shuffled entrapment sequences. 
Download the zipped FASTA file here: [TOADD](https://proteobench.cubimed.rub.de/fasta/TOADD).

## Metric calculation

The false discovery proportion (FDP) is calculated using the paired entrapment strategy for FDR control evaluation described in [Wen, B., Freestone, J., Riffle, M. et al., 2025](https://doi-org.insb.bib.cnrs.fr/10.1038/s41592-025-02719-x) and implemented in [FDRBench](https://github.com/Noble-Lab/FDRBench).
