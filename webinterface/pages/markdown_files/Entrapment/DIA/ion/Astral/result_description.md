It contains the following columns:

- **precursor ion**: precursor-level identifier used for deduplication
- **Sequence**: modified peptide sequence
- **Peptide**: stripped peptide sequence used for entrapment mapping
- **Charge**: precursor charge
- **Q-Value**: precursor-level FDR value parsed from the submitted output
- **Target or Entrapment**: target/entrapment classification from the ProteoBench mapping file
- **peptide_pair_index**: identifier linking each entrapment peptide to its paired target peptide
- **Lower bound FDP**, **Combined FDP**, and **Paired FDP**: empirical FDP estimates used to classify the submitted workflow
