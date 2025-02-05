import os

from proteobench.io.parsing.parse_proteins import load_input_file
from proteobench.io.parsing.parse_settings import ParseSettingsBuilder

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), "data/subcellprofile_domlfq_protein_DIA_EXPL")
TESTDATA_FILES = {
    "DIA-NN": os.path.join(TESTDATA_DIR, "DIA-NN_example_domlfq_report.pg_matrix.tsv"),
}
PARSE_SETTINGS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "proteobench",
        "io",
        "parsing",
        "io_parse_settings",
        "subcellprofile",
        "domlfq",
        "protein",
        "DIA",
    )
)


def load_file(format_name: str):
    """Method used to load the input file."""
    input_df = load_input_file(TESTDATA_FILES[format_name], format_name)
    return input_df

class TestOutputFileReading:
    supported_formats = (
        "DIA-NN",
    )
    """Simple tests for reading csv input files."""

    def test_valid_and_supported_search_tool_settings_exists(self):
        """Test whether the supported formats are existing and  valid."""
        parse_settings = ParseSettingsBuilder(parse_settings_dir=PARSE_SETTINGS_DIR, module_id="subcellprofile_domlfq_protein_DIA_EXPL")

        for format_name in self.supported_formats:
            assert format_name in parse_settings.INPUT_FORMATS

    def test_if_module_supports_search_tool(self):
        """Test whether the supported formats are existing and  valid."""
        parse_settings = ParseSettingsBuilder(parse_settings_dir=PARSE_SETTINGS_DIR, module_id="subcellprofile_domlfq_protein_DIA_EXPL")

        for input_format in parse_settings.INPUT_FORMATS:
            assert input_format in self.supported_formats

    def test_input_file_loading(self):
        """Test whether the inputs input are loaded successfully."""
        for format_name in self.supported_formats:
            input_df = load_file(format_name)
            assert not input_df.empty

    def test_creation_of_parser_settings_instance(self):
        """Test whether the input files are loaded successfully."""

        parse_settings_builder = ParseSettingsBuilder(
            module_id="subcellprofile_domlfq_protein_DIA_EXPL", parse_settings_dir=PARSE_SETTINGS_DIR
        )
        for format_name in self.supported_formats:
            parse_settings = parse_settings_builder.build_parser(format_name)
            assert parse_settings is not None

    def test_input_file_initial_parsing(self):
        """Test the initial parsing of the input file."""

        parse_settings_builder = ParseSettingsBuilder(
            module_id="subcellprofile_domlfq_protein_DIA_EXPL", parse_settings_dir=PARSE_SETTINGS_DIR
        )

        for format_name in self.supported_formats:
            input_df = load_file(format_name)
            parse_settings = parse_settings_builder.build_parser(format_name)
            prepared_df, replicate_to_raw = parse_settings.convert_to_standard_format(input_df)

            assert not prepared_df.empty
            assert replicate_to_raw != {}
