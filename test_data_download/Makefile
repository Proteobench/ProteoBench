.PHONY: help catalog select download clean

.DEFAULT_GOAL := help

help:  ## Show this help message.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

catalog: raw_file_db_full.csv  ## Build the full catalog CSV by downloading datapoint JSONs for all 8 quant modules.

raw_file_db_full.csv:
	uv run python extract_raw_file_db.py catalog \
		--json-dir ./json_dir \
		--output ./raw_file_db_full.csv

select: raw_file_db_selected.csv  ## Reduce the catalog to one row per (module, software, version) -> raw_file_db_selected.csv.

raw_file_db_selected.csv: raw_file_db_full.csv
	uv run python extract_raw_file_db.py select \
		--input ./raw_file_db_full.csv \
		--output ./raw_file_db_selected.csv

download: raw_file_db_selected.csv  ## Download raw quantification files for the selected rows -> raw_file_db_downloaded.csv.
	uv run python extract_raw_file_db.py download \
		--input ./raw_file_db_selected.csv \
		--json-dir ./json_dir \
		--output ./raw_file_db_downloaded.csv

clean:  ## Remove downloaded JSON folders and all CSVs.
	rm -rf ./json_dir ./raw_file_db_full.csv ./raw_file_db_selected.csv ./raw_file_db_downloaded.csv
