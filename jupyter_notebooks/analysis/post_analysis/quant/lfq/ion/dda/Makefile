# Makefile for running notebooks and exporting to HTML
#
# Usage:
#   make all                        - Export all notebooks to HTML
#   make marimo                     - Export all marimo notebooks to HTML
#   make jupyter                    - Export all Jupyter notebooks to HTML
#   make roc_auc_analysis.html      - Export specific marimo notebook
#   make indepth_module_analysis.html - Export specific Jupyter notebook
#   make clean                      - Remove generated HTML files

# Marimo notebooks (.py)
MARIMO_NOTEBOOKS := roc_auc_analysis.py scores_dissected.py
MARIMO_HTML := $(MARIMO_NOTEBOOKS:.py=.html)

# Jupyter notebooks (.ipynb)
# Note: plot_runs_sage.ipynb uses obsolete modules (proteobench.utils.quant_datapoint)
# Note: comparison_across_datapoints.ipynb removed - redundant with indepth_module_analysis.ipynb
JUPYTER_NOTEBOOKS := indepth_module_analysis.ipynb \
                     DDA_ion_quant_manuscript.ipynb
JUPYTER_HTML := $(JUPYTER_NOTEBOOKS:.ipynb=.html)

.PHONY: all marimo jupyter clean help

help:
	@echo "Usage:"
	@echo "  make all                          - Export all notebooks to HTML"
	@echo "  make marimo                       - Export all marimo notebooks to HTML"
	@echo "  make jupyter                      - Export all Jupyter notebooks to HTML"
	@echo "  make roc_auc_analysis.html        - Export specific marimo notebook"
	@echo "  make scores_dissected.html        - Export specific marimo notebook"
	@echo "  make indepth_module_analysis.html - Export specific Jupyter notebook"
	@echo "  make clean                        - Remove generated HTML files"
	@echo "  make help                         - Show this help message"

all: marimo jupyter

marimo: $(MARIMO_HTML)

jupyter: $(JUPYTER_HTML)

# Rule for marimo notebooks (--no-sandbox uses the current environment)
%.html: %.py
	marimo export html --no-sandbox $< -o $@

# Rule for Jupyter notebooks
%.html: %.ipynb
	jupyter nbconvert --to html --execute --no-input $<

clean:
	rm -f $(MARIMO_HTML) $(JUPYTER_HTML)
