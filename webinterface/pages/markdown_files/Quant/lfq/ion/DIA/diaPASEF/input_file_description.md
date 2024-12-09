Please upload the ouput of your analysis, and indicate what software 
tool it comes from (this is necessary to correctly parse your table - find 
more information in the "[How to use](https://proteobench.readthedocs.io/en/stable/available-modules/4-quant-lfq-ion-dia-aif/)"
section of this module).

Currently, we support output files from AlphaDIA and DIA-NN. It is also possible to reformat your data in a tab-delimited file that we call "custom format" in the [documentation](https://proteobench.readthedocs.io/en/latest/available-modules/4-quant-lfq-ion-dia-aif/). We are still working on EncyclopeDIA, MSFraggerDIA, Skyline and Spectronaut.

Remember: contaminant sequences are already present in the fasta file 
associated to this module. **Do not add other contaminants** to your 
search. This is important when using MaxQuant and FragPipe, among other tools.
