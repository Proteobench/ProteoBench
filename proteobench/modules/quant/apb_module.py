"""Quant module implementation backed by APB parsing and scoring."""

from __future__ import annotations

import os
import zipfile
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory
from typing import Any

import pandas as pd
from apb2.api import parse_search_parameters, write_parsed_levels
from apb2.result_facade import sidecar_path

from proteobench.io.params import ProteoBenchParameters
from proteobench.modules.quant.apb_workflow import APBQuantAnalysis, analyze_quant_upload
from proteobench.modules.quant.quant_base_module import QuantModule


class APBQuantModule(QuantModule):
    """Share the APB upload path across the HYE/HY quant modules."""

    apb_module_name: str
    last_apb_analysis: APBQuantAnalysis | None = None

    def load_params_file(self, input_file: list[Any], input_format: str, json_file: str) -> ProteoBenchParameters:
        """Read optional search metadata with APB2 for the submission form."""
        if not input_file:
            raise ValueError("No search-parameter files were uploaded")
        software = {"FragPipe (DIA-NN quant)": "FragPipe"}.get(input_format, input_format)
        sources = tuple(Path(item) if isinstance(item, str) else item for item in input_file)
        parsed = parse_search_parameters(sources[0] if len(sources) == 1 else sources, software=software)
        values = parsed.model_dump(mode="json")
        for name in ("ident_fdr_psm", "ident_fdr_peptide", "ident_fdr_protein"):
            values[name] = values[name]["value"] if values[name] is not None else None
        for name in ("precursor_mass_tolerance", "fragment_mass_tolerance"):
            tolerance = values[name]
            if tolerance is not None:
                values[name] = (
                    "Automatic calibration"
                    if tolerance["mode"] == "automatic"
                    else f"{tolerance['value']} {tolerance['unit']}"
                )
        for name in ("fixed_mods", "variable_mods"):
            values[name] = "; ".join(item["name"] for item in values[name]) or None
        parameters = ProteoBenchParameters(filename=json_file)
        for name in parameters.__dict__:
            if name in values and values[name] is not None:
                setattr(parameters, name, values[name])
        parameters.software_name = input_format
        parameters.fill_none()
        return parameters

    def write_intermediate_raw(
        self,
        directory: str,
        ident: str,
        input_file_obj: Any,
        result_performance: pd.DataFrame,
        param_loc: list[Any],
        comment: str,
        extension_input_file: str = ".txt",
        extension_input_parameter_file: str = ".txt",
        input_file_secondary_obj: Any = None,
        *,
        analysis: APBQuantAnalysis | None = None,
    ) -> None:
        """Archive the raw upload, pMultiQC CSV and scored H5AD atomically."""
        scored = analysis or self.last_apb_analysis
        if scored is None:
            raise ValueError("No scored APB result is available for archival")
        if ident != scored.content_hash:
            raise ValueError("Archive identity does not match the scored APB result")
        target_dir = Path(directory) / ident
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{ident}_data.zip"
        if target.exists():
            raise FileExistsError(f"Submission archive already exists: {target}")
        with TemporaryDirectory(prefix="proteobench-archive-", dir=target_dir) as temporary:
            staging = Path(temporary)
            h5ad = staging / "scored.h5ad"
            write_parsed_levels(scored.result.parsed, h5ad)
            archive = staging / "submission.zip"
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                input_file_obj.seek(0)
                bundle.writestr(f"input_file{extension_input_file}", input_file_obj.read())
                if input_file_secondary_obj is not None:
                    input_file_secondary_obj.seek(0)
                    extension = Path(input_file_secondary_obj.name).suffix
                    bundle.writestr(f"input_file_secondary{extension}", input_file_secondary_obj.read())
                bundle.writestr("result_performance.csv", result_performance.to_csv(index=False))
                for index, parameter in enumerate(param_loc):
                    parameter.seek(0)
                    extension = Path(parameter.name).suffix or extension_input_parameter_file
                    bundle.writestr(f"param_{index}{extension}", parameter.read())
                bundle.writestr("comment.txt", comment)
                bundle.write(h5ad, h5ad.name)
                representation = sidecar_path(h5ad)
                bundle.write(representation, representation.name)
            os.link(archive, target)

    def benchmarking(
        self,
        input_file: str,
        input_format: str,
        user_input: dict[str, Any],
        all_datapoints: pd.DataFrame | None,
        default_cutoff_min_feature: int = 3,
        input_file_secondary: str | None = None,
        max_nr_observed: int | None = None,
    ) -> tuple[pd.DataFrame, pd.DataFrame, APBQuantAnalysis]:
        """Parse and score a raw upload with APB and project current UI values."""
        source = Path(input_file)
        if input_file_secondary is None:
            analysis = analyze_quant_upload(source, software=input_format, module=self.apb_module_name)
        else:
            secondary = Path(input_file_secondary)
            if source.name == secondary.name:
                raise ValueError("APB multifile uploads need distinct result filenames")
            with TemporaryDirectory(prefix="proteobench-apb-") as temporary:
                directory = Path(temporary)
                copyfile(source, directory / source.name)
                copyfile(secondary, directory / secondary.name)
                analysis = analyze_quant_upload(directory, software=input_format, module=self.apb_module_name)
        self.last_apb_analysis = analysis
        current = analysis.datapoint(
            input_format=input_format,
            user_input=user_input,
            cutoff=default_cutoff_min_feature,
        )
        datapoints = self.add_current_data_point(current, all_datapoints=all_datapoints)
        return analysis.intermediate, datapoints, analysis
