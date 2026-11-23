"""Tests for the programmatic submission path in `proteobench.utils.server_io`.

The module families expose deliberately different `benchmarking()` signatures, so these tests
use stub modules shaped like each family rather than the real classes: the real ones clone
GitHub repos and read multi-megabyte inputs, and what needs testing here is the orchestration.
"""

import pandas as pd
import pytest

from proteobench.modules.denovo.denovo_DDA_HCD import DDAHCDDeNovoModule
from proteobench.utils import server_io


class StubParams:
    """Stands in for `ProteoBenchParameters`, including its two flavours of absent value."""

    def __init__(self):
        self.software_version = "1.2.2"
        self.decoding_strategy = "beam search"
        self.n_beams = 10
        self.enzyme = None
        self.fragment_mass_tolerance = float("nan")
        self.isotope_error_range = [0, 1]


class StubModuleBase:
    """Records what `make_submission` passed, so the orchestration can be asserted on."""

    created = []

    def __init__(self, token=""):
        self.token = token
        self.user_input = None
        self.benchmarking_kwargs = None
        self.clone_call = None
        type(self).created.append(self)

    def obtain_all_data_points(self, all_datapoints=None):
        return pd.DataFrame({"id": ["existing"]})

    def load_params_file(self, input_file, input_format, **kwargs):
        self.param_files = input_file
        return StubParams()

    def clone_pr(
        self,
        temporary_datapoints,
        datapoint_params,
        remote_git,
        submission_comments="no comments",
        submission_source="unknown",
    ):
        self.clone_call = {
            "submission_comments": submission_comments,
            "submission_source": submission_source,
            "datapoint_params": datapoint_params,
        }
        return f"https://github.com/Proteobot/pull/{len(type(self).created)}"


class StubDeNovoModule(StubModuleBase):
    """Signature of `DDAHCDDeNovoModule.benchmarking`: takes `evaluation_type`."""

    created = []

    def benchmarking(
        self,
        input_file_loc,
        input_format,
        user_input,
        all_datapoints,
        evaluation_type="mass",
        input_file_secondary=None,
    ):
        self.user_input = user_input
        self.benchmarking_kwargs = {"evaluation_type": evaluation_type}
        return "intermediate", all_datapoints, "parsed_input"


class StubQuantModule(StubModuleBase):
    """Signature of `QuantModule.benchmarking`: takes `default_cutoff_min_feature`."""

    created = []

    def benchmarking(
        self,
        input_file,
        input_format,
        user_input,
        all_datapoints,
        default_cutoff_min_feature=3,
        input_file_secondary=None,
        max_nr_observed=None,
    ):
        self.user_input = user_input
        self.benchmarking_kwargs = {
            "default_cutoff_min_feature": default_cutoff_min_feature,
            "max_nr_observed": max_nr_observed,
        }
        return "intermediate", all_datapoints, "parsed_input"


@pytest.fixture
def stub_modules(monkeypatch):
    """Register both stubs and clear their per-test call records."""
    StubDeNovoModule.created = []
    StubQuantModule.created = []
    monkeypatch.setitem(server_io.MODULE_CLASSES, "StubDeNovoModule", StubDeNovoModule)
    monkeypatch.setitem(server_io.MODULE_CLASSES, "StubQuantModule", StubQuantModule)


def base_submission(**extra):
    return dict(input_file="results.csv", input_type="InstaNovo", param_file="config.yaml", **extra)


class TestModuleRegistry:
    def test_denovo_module_is_registered(self):
        """The de novo module must be reachable by name, or scripted submission is impossible."""
        assert server_io.MODULE_CLASSES["DDAHCDDeNovoModule"] is DDAHCDDeNovoModule

    def test_registry_keys_match_class_names(self):
        for name, module_class in server_io.MODULE_CLASSES.items():
            assert module_class.__name__ == name


class TestSignatureFiltering:
    def test_denovo_receives_evaluation_type_and_not_the_quant_knob(self, stub_modules):
        """A de novo submission carrying both knobs must not raise TypeError."""
        server_io.make_submission(
            submission_files=[base_submission(evaluation_type="exact", default_cutoff_min_feature=3)],
            module_name="StubDeNovoModule",
        )
        assert StubDeNovoModule.created[0].benchmarking_kwargs == {"evaluation_type": "exact"}

    def test_quant_receives_its_own_knobs(self, stub_modules):
        server_io.make_submission(
            submission_files=[base_submission(default_cutoff_min_feature=4, evaluation_type="exact")],
            module_name="StubQuantModule",
        )
        assert StubQuantModule.created[0].benchmarking_kwargs == {
            "default_cutoff_min_feature": 4,
            "max_nr_observed": None,
        }

    def test_omitted_knobs_fall_back_to_module_defaults(self, stub_modules):
        server_io.make_submission(submission_files=[base_submission()], module_name="StubDeNovoModule")
        assert StubDeNovoModule.created[0].benchmarking_kwargs == {"evaluation_type": "mass"}


class TestUserInputSeeding:
    def test_user_input_is_seeded_from_the_parsed_params(self, stub_modules):
        """Without this the datapoint id, and so the PR branch name, carries empty metadata."""
        server_io.make_submission(submission_files=[base_submission()], module_name="StubDeNovoModule")
        user_input = StubDeNovoModule.created[0].user_input
        assert user_input["software_version"] == "1.2.2"
        assert user_input["decoding_strategy"] == "beam search"
        assert user_input["n_beams"] == 10

    def test_absent_params_do_not_leak_none_or_nan(self, stub_modules):
        """`ProteoBenchParameters` uses both None and NaN for "absent"; neither belongs in an id."""
        server_io.make_submission(submission_files=[base_submission()], module_name="StubDeNovoModule")
        user_input = StubDeNovoModule.created[0].user_input
        assert user_input["enzyme"] == ""
        assert user_input["fragment_mass_tolerance"] == ""

    def test_list_valued_params_survive(self, stub_modules):
        """`pd.isna` on a list returns an array, which must not be mistaken for "absent"."""
        server_io.make_submission(submission_files=[base_submission()], module_name="StubDeNovoModule")
        assert StubDeNovoModule.created[0].user_input["isotope_error_range"] == [0, 1]

    def test_comments_reach_both_the_datapoint_and_the_pull_request(self, stub_modules):
        server_io.make_submission(
            submission_files=[base_submission(user_comments="beam 10, refined")],
            module_name="StubDeNovoModule",
        )
        module = StubDeNovoModule.created[0]
        assert module.user_input["comments_for_plotting"] == "beam 10, refined"
        assert module.clone_call["submission_comments"] == "beam 10, refined"


class TestSubmissionLoop:
    def test_every_submission_produces_a_url(self, stub_modules):
        """The loop used to return inside its first iteration, silently dropping the rest."""
        urls = server_io.make_submission(
            submission_files=[base_submission(), base_submission(), base_submission()],
            module_name="StubDeNovoModule",
        )
        assert len(urls) == 3
        assert len(StubDeNovoModule.created) == 3

    def test_no_submissions_is_not_an_error(self, stub_modules):
        assert server_io.make_submission(submission_files=[], module_name="StubDeNovoModule") == []
        assert server_io.make_submission(module_name="StubDeNovoModule") == []

    def test_token_reaches_the_module(self, stub_modules):
        """The token was hardcoded to "", leaving clone_pr unable to push."""
        server_io.make_submission(
            submission_files=[base_submission()], token="ghp_example", module_name="StubDeNovoModule"
        )
        assert StubDeNovoModule.created[0].token == "ghp_example"

    def test_submission_source_defaults_to_the_batch_label(self, stub_modules):
        server_io.make_submission(submission_files=[base_submission()], module_name="StubDeNovoModule")
        assert StubDeNovoModule.created[0].clone_call["submission_source"] == "resubmission-script"

    def test_submission_source_is_forwarded(self, stub_modules):
        server_io.make_submission(
            submission_files=[base_submission()], module_name="StubDeNovoModule", submission_source="local"
        )
        assert StubDeNovoModule.created[0].clone_call["submission_source"] == "local"


class TestValidation:
    def test_unknown_module_raises_even_with_no_submissions(self, stub_modules):
        """The check used to sit inside the loop, so an empty list hid the bad name."""
        with pytest.raises(ValueError, match="not recognized"):
            server_io.make_submission(submission_files=[], module_name="NoSuchModule")

    def test_unknown_module_lists_the_available_ones(self, stub_modules):
        with pytest.raises(ValueError, match="DDAHCDDeNovoModule"):
            server_io.make_submission(submission_files=[base_submission()], module_name="NoSuchModule")

    @pytest.mark.parametrize("missing_key", ["input_file", "input_type", "param_file"])
    def test_missing_required_key_names_it(self, stub_modules, missing_key):
        """A bare `except: continue` used to swallow this and skip the submission silently."""
        submission = base_submission()
        del submission[missing_key]
        with pytest.raises(KeyError, match=missing_key):
            server_io.make_submission(submission_files=[submission], module_name="StubDeNovoModule")

    def test_param_parsing_failure_is_not_swallowed(self, stub_modules, monkeypatch):
        def explode(self, input_file, input_format, **kwargs):
            raise ValueError("unreadable metadata file")

        monkeypatch.setattr(StubDeNovoModule, "load_params_file", explode)
        with pytest.raises(ValueError, match="unreadable metadata file"):
            server_io.make_submission(submission_files=[base_submission()], module_name="StubDeNovoModule")


class TestIsMissing:
    @pytest.mark.parametrize("value", [None, float("nan")])
    def test_absent_values(self, value):
        assert server_io._is_missing(value) is True

    @pytest.mark.parametrize("value", ["", 0, 10, "beam search", [0, 1], ["a", "b"]])
    def test_present_values(self, value):
        assert server_io._is_missing(value) is False
