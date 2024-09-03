Please upload the ouput of your analysis, and indicate what software 
tool it comes from (this is necessary to correctly parse your table - find 
more information in the "[How to use](https://proteobench.readthedocs.io/en/stable/available-modules/2-DDA-Quantification-ion-level/#how-to-use)" 
section of this module).

Currently, we support output files from AlphaPept, MaxQuant, Proline and Sage. It is also possible to reformat your data in a tab-delimited file that we call "custom format" in the [documentation](https://proteobench.readthedocs.io/en/stable/available-modules/2-DDA-Quantification-ion-level/#custom-format).

Remember: contaminant sequences are already present in the fasta file 
associated to this module. **Do not add other contaminants** to your 
search. This is important when using MaxQuant and FragPipe, among other tools.
