# Large Files in jupyter_notebooks

**Total size**: 42GB  
**Files > 1MB**: 503 files

## Issue
The `jupyter_notebooks/` directory contains numerous large temporary and extracted files that should be reviewed for:
- Cleanup (if no longer needed)
- Addition to `.gitignore` (if regenerated during analysis)
- External storage strategy (if needed for reference)

## Large Files Summary

### Largest File Categories

#### input_file.* (Various formats: .txt, .csv, .tsv)
- 42M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/temp_results/Results_quant_ion_DDA/e0ab1339a5354cb27d895ff252383ee4a3365b2e/input_file.txt`
- 42M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/dda/temp_results/e0ab1339a5354cb27d895ff252383ee4a3365b2e/input_file.txt`
- 42M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/dda/extracted_files/e0ab1339a5354cb27d895ff252383ee4a3365b2e/input_file.txt`
- 41M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/temp_results/Results_quant_ion_DIA_Astral/b342522520beee8fa15304c6683eed7a2f68e01f/input_file.csv`
- 41M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/temp_results/Results_quant_ion_DIA_Astral/649792bdaf1bb9e371d5c261dc7bfd7d42a84df6/input_file.csv`
- 39M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/temp_results/Results_quant_ion_DDA/90d852742aa152dc7ed813acebf7916b0c1d5b76/input_file.tsv`
- 39M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/dda/temp_results/90d852742aa152dc7ed813acebf7916b0c1d5b76/input_file.tsv`
- 38M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/temp_results/Results_quant_ion_DIA_ZenoTOF/d08f2cb6e471eaa24bddaef80ee04cdbfb4f8d79/input_file.csv`
- 37M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/temp_results/Results_quant_ion_DDA/28b0c3b9853a5b60c9e47428b8a51b4898083523/input_file.tsv`
- 38M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/temp_results/Results_quant_ion_DIA_AIF/b5fddd9b5d27918e8d31ec07bcf599cbd214027a/input_file.txt`

#### result_performance.csv
- 42M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/temp_results/Results_quant_ion_DIA_Astral/2eb6ecaa7ea57027adfdfd5db564f0a3d536f494/result_performance.csv`
- 41M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/temp_results/Results_quant_ion_DIA_Astral/a2c68b9d5ad8a620af53513c91a9aa2b0f2584f1/result_performance.csv`
- 40M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/temp_results/Results_quant_ion_DIA_Astral/deb0844196e184b7eccd1c77487a2e0d4dafdad1/result_performance.csv`
- 40M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/temp_results/Results_quant_ion_DIA_Astral/aa1d53e859aae10d0f5b991862bc2dedbf2f79f6/result_performance.csv`
- 39M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/temp_results/Results_quant_ion_DIA_Astral/c572ba8406c3a04d30b2f4e3c29ae6fb9328fede/result_performance.csv`
- 39M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/temp_results/Results_quant_ion_DIA_diaPASEF/402b66d39dbe7ba3e3dca408e199b368e7d1d8b7/result_performance.csv`
- 39M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/temp_results/Results_quant_ion_DDA/2a5ef6191b8098757d490acf76bb9c2af5b89a39/input_file.txt`
- 38M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/temp_results/Results_quant_ion_DIA_Astral/b342522520beee8fa15304c6683eed7a2f68e01f/result_performance.csv`
- 38M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/temp_results/Results_quant_ion_DIA_Astral/d8c5c375affccf0657f4bd44279d87e41cc41df6/result_performance.csv`
- 38M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/temp_results/Results_quant_ion_DIA_Astral/be4d3e067a35ae1e2cca00cdfaae525268bbde90/result_performance.csv`

#### SVG Graphics
- 41M `/Users/wolski/projects/ProteoBench/jupyter_notebooks/analysis/post_analysis/quant/lfq/ion/dda/figures_manuscript/pair_quantifications.svg`

## Directory Structure
- `temp_results/` - Temporary benchmark result files
- `extracted_files/` - Extracted/unpacked benchmark files (duplicates of temp_results)
- `figures_manuscript/` - Generated manuscript figures (includes large SVG)

## Actions Needed
- [ ] Review purpose of temp_results and extracted_files directories
- [ ] Determine if files are actively used or can be deleted
- [ ] Consider adding directories to `.gitignore`
- [ ] Review if manuscript figures need to be in version control
- [ ] Consider external storage for reference data if needed
