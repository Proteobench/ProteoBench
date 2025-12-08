# Makefile for benchmark analysis notebooks
#
# Usage:
#   make help           - Show this help
#   make all            - Export all module notebooks to HTML
#   make dda            - Export all DDA modules
#   make dia            - Export all DIA modules
#   make clean          - Remove generated HTML files

# All modules
MODULES = dda_qexactive dda_astral dda_peptidoform \
          dia_astral dia_diapasef dia_aif dia_zenotof dia_singlecell dia_peptidoform

# DDA modules
DDA_MODULES = dda_qexactive dda_astral dda_peptidoform

# DIA modules
DIA_MODULES = dia_astral dia_diapasef dia_aif dia_zenotof dia_singlecell dia_peptidoform

.PHONY: all help clean dda dia $(MODULES)

help:
	@echo "Benchmark Analysis Notebooks"
	@echo ""
	@echo "Usage:"
	@echo "  make all              - Export all module notebooks to HTML"
	@echo "  make dda              - Export all DDA modules"
	@echo "  make dia              - Export all DIA modules"
	@echo "  make clean            - Remove generated HTML files"
	@echo ""
	@echo "DDA modules:"
	@echo "  make dda_qexactive    - DDA Q-Exactive ion-level"
	@echo "  make dda_astral       - DDA Astral ion-level"
	@echo "  make dda_peptidoform  - DDA peptidoform-level"
	@echo ""
	@echo "DIA modules:"
	@echo "  make dia_astral       - DIA Astral ion-level"
	@echo "  make dia_diapasef     - DIA diaPASEF ion-level"
	@echo "  make dia_aif          - DIA AIF ion-level"
	@echo "  make dia_zenotof      - DIA ZenoTOF ion-level"
	@echo "  make dia_singlecell   - DIA Single-Cell ion-level"
	@echo "  make dia_peptidoform  - DIA peptidoform-level"

all: $(MODULES)
dda: $(DDA_MODULES)
dia: $(DIA_MODULES)

# Generic rule: each module depends on its HTML file
$(MODULES): %: %.html

# Generic rule: generate HTML from benchmark_analysis.py with --module arg
%.html: benchmark_analysis.py
	marimo export html --no-sandbox $< -o $@ -- --module $*

clean:
	rm -f $(addsuffix .html,$(MODULES))
