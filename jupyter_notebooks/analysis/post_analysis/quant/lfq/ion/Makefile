# Makefile for benchmark analysis notebooks
#
# Usage:
#   make help           - Show this help
#   make all            - Export all module notebooks to HTML + index
#   make dda            - Export all DDA modules
#   make dia            - Export all DIA modules
#   make index          - Generate index.html only
#   make clean          - Remove generated HTML files
#   make zip            - Create timestamped zip archive of HTML files
#   make deploy         - Deploy latest zip to server
#   make refresh        - Re-download from GitHub and rebuild all
#   make refresh-MODULE - Re-download and rebuild specific module

# All modules (short keys used for --module arg)
# NOTE: dia_peptidoform excluded - repo is empty (no data yet)
MODULES = dda_qexactive dda_astral dda_peptidoform \
          dia_astral dia_diapasef dia_aif dia_zenotof dia_singlecell

# DDA modules
DDA_MODULES = dda_qexactive dda_astral dda_peptidoform

# DIA modules (dia_peptidoform excluded - repo empty)
DIA_MODULES = dia_astral dia_diapasef dia_aif dia_zenotof dia_singlecell

# Output HTML filenames (using module class names)
HTML_dda_qexactive = DDAQuantIonModuleQExactive.html
HTML_dda_astral = DDAQuantIonAstralModule.html
HTML_dda_peptidoform = DDAQuantPeptidoformModule.html
HTML_dia_astral = DIAQuantIonModuleAstral.html
HTML_dia_diapasef = DIAQuantIonModulediaPASEF.html
HTML_dia_aif = DIAQuantIonModuleAIF.html
HTML_dia_zenotof = DIAQuantIonModuleZenoTOF.html
HTML_dia_singlecell = DIAQuantIonModulediaSC.html
HTML_dia_peptidoform = DIAQuantPeptidoformModule.html

# All HTML files
HTML_FILES = $(foreach m,$(MODULES),$(HTML_$(m)))

# Use uv run to ensure marimo is available
# MARIMO = uv run marimo
MARIMO = marimo

# Export marimo notebook to HTML, fail and remove output if errors occur
# Usage: $(call marimo_export,input.py,output.html,module_arg)
# --no-include-code hides code cells, showing only markdown and outputs
define marimo_export
	$(MARIMO) export html --no-sandbox --no-include-code $(1) -o $(2) $(3) 2>&1 | tee /dev/stderr | (! grep -q "MarimoExceptionRaisedError") || (rm -f $(2) && false)
endef

# Deployment settings
DEPLOY_USER = wolski
DEPLOY_HOST = fgcz-r-035.uzh.ch
DEPLOY_PATH = /srv/www/htdocs/public/proteobench

.PHONY: all help clean dda dia index refresh clean-json zip deploy $(MODULES)

help:
	@echo "Benchmark Analysis Notebooks"
	@echo ""
	@echo "Usage:"
	@echo "  make all              - Export all module notebooks to HTML + index"
	@echo "  make dda              - Export all DDA modules"
	@echo "  make dia              - Export all DIA modules"
	@echo "  make index            - Generate index.html only"
	@echo "  make clean            - Remove generated HTML files"
	@echo "  make zip              - Create timestamped zip archive of HTML files"
	@echo "  make deploy           - Deploy latest zip to $(DEPLOY_HOST):$(DEPLOY_PATH)"
	@echo "  make refresh          - Re-download from GitHub and rebuild all"
	@echo "  make refresh-MODULE   - Re-download and rebuild specific module"
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

all: $(MODULES) index
dda: $(DDA_MODULES)
dia: $(DIA_MODULES)

# Index page
index: index.html

index.html: index.py
	$(call marimo_export,$<,$@,)

# Module targets - each depends on its HTML file with full class name
dda_qexactive: $(HTML_dda_qexactive)
dda_astral: $(HTML_dda_astral)
dda_peptidoform: $(HTML_dda_peptidoform)
dia_astral: $(HTML_dia_astral)
dia_diapasef: $(HTML_dia_diapasef)
dia_aif: $(HTML_dia_aif)
dia_zenotof: $(HTML_dia_zenotof)
dia_singlecell: $(HTML_dia_singlecell)
dia_peptidoform: $(HTML_dia_peptidoform)

# Build rules for each module
$(HTML_dda_qexactive): benchmark_analysis.py
	$(call marimo_export,$<,$@,-- --module dda_qexactive)

$(HTML_dda_astral): benchmark_analysis.py
	$(call marimo_export,$<,$@,-- --module dda_astral)

$(HTML_dda_peptidoform): benchmark_analysis.py
	$(call marimo_export,$<,$@,-- --module dda_peptidoform)

$(HTML_dia_astral): benchmark_analysis.py
	$(call marimo_export,$<,$@,-- --module dia_astral)

$(HTML_dia_diapasef): benchmark_analysis.py
	$(call marimo_export,$<,$@,-- --module dia_diapasef)

$(HTML_dia_aif): benchmark_analysis.py
	$(call marimo_export,$<,$@,-- --module dia_aif)

$(HTML_dia_zenotof): benchmark_analysis.py
	$(call marimo_export,$<,$@,-- --module dia_zenotof)

$(HTML_dia_singlecell): benchmark_analysis.py
	$(call marimo_export,$<,$@,-- --module dia_singlecell)

$(HTML_dia_peptidoform): benchmark_analysis.py
	$(call marimo_export,$<,$@,-- --module dia_peptidoform)

clean:
	rm -f $(HTML_FILES) index.html

# Create timestamped zip archive of all HTML files
zip:
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S) && \
	zip -j proteobench_reports_$${TIMESTAMP}.zip $(HTML_FILES) index.html && \
	echo "Created proteobench_reports_$${TIMESTAMP}.zip"

# Refresh targets - delete cached JSONs to force re-download from GitHub
refresh: clean-json clean all

clean-json:
	rm -rf temp_results/*/Results_*-main/

# Deploy to server - create zip, scp it, and extract
deploy: zip
	@ZIPFILE=$$(ls -t proteobench_reports_*.zip 2>/dev/null | head -1) && \
	if [ -z "$$ZIPFILE" ]; then \
		echo "Error: No proteobench_reports_*.zip found. Run 'make zip' first."; \
		exit 1; \
	fi && \
	echo "Deploying $$ZIPFILE to $(DEPLOY_USER)@$(DEPLOY_HOST):$(DEPLOY_PATH)" && \
	scp "$$ZIPFILE" $(DEPLOY_USER)@$(DEPLOY_HOST):$(DEPLOY_PATH)/ && \
	ssh $(DEPLOY_USER)@$(DEPLOY_HOST) "cd $(DEPLOY_PATH) && unzip -o $$ZIPFILE" && \
	echo "Deployment complete!"
