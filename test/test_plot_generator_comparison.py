"""
Tests for the workflow-comparison contract of the LFQ plot generators.

The "Compare Two Results" tab is driven entirely by three methods on a module's plot generator:
``get_comparison_plot_layout`` declares the tabs, ``generate_comparison_plots`` supplies the
figures, and ``get_comparison_plot_descriptions`` supplies the text under each tab title. The
``name`` key is the contract between them, so these tests guard that a generator cannot declare
a tab the web interface is then unable to render.

The contract lives on :class:`LFQHYEPlotGenerator`, not on the abstract base, because it assumes
the LFQ intermediate schema: features identified by a precursor ion or peptidoform column, and
per-condition intensity means. The de novo and entrapment modules use a different schema and do
not reach the comparison tab at all, so they must not carry these methods.
"""

import numpy as np
import pandas as pd
import pytest
from plotly import graph_objects as go

from proteobench.plotting.plot_generator_base import PlotGeneratorBase
from proteobench.plotting.plot_generator_denovo import DeNovoPlotGenerator
from proteobench.plotting.plot_generator_entrapment import EntrapmentPlotGenerator
from proteobench.plotting.plot_generator_lfq_HYE import LFQHYEPlotGenerator
from proteobench.plotting.plot_generator_lfq_lowinput import LFQLowInputPlotGenerator
from proteobench.plotting.plot_generator_lfq_PYE import LFQPYEPlotGenerator

# Tab names the web interface renders itself (they combine a figure with Streamlit widgets)
# rather than looking them up in ``generate_comparison_plots``.
BUILTIN_TAB_NAMES = ("precursor_overlap", "parameter_differences")

# The LFQ quant generators, which share the intermediate schema the comparison tab assumes and
# therefore inherit the comparison contract from LFQHYEPlotGenerator.
LFQ_GENERATORS = [
    LFQHYEPlotGenerator,
    LFQLowInputPlotGenerator,
    LFQPYEPlotGenerator,
]

# Generators for modules that use a different intermediate schema and never reach the comparison
# tab: de novo routes its "Compare Results" tab to the in-depth plots, and entrapment shows an
# "under development" placeholder.
NON_LFQ_GENERATORS = [
    DeNovoPlotGenerator,
    EntrapmentPlotGenerator,
]

# Methods that make up the workflow-comparison contract.
COMPARISON_CONTRACT = (
    "plot_precursor_overlap",
    "generate_comparison_plots",
    "get_comparison_plot_layout",
    "get_comparison_plot_descriptions",
)


def make_intermediate(n_precursors: int = 300, noise: float = 0.3, seed: int = 0) -> pd.DataFrame:
    """Build a synthetic HYE intermediate table with the columns the comparison plots need."""
    rng = np.random.default_rng(seed)
    species = rng.choice(["HUMAN", "YEAST", "ECOLI"], n_precursors)
    expected_ratio = {"HUMAN": 0.0, "YEAST": -1.0, "ECOLI": 2.0}
    abundance = rng.normal(20, 2, n_precursors)

    return pd.DataFrame(
        {
            "precursor ion": [f"PEPTIDE{i}/2" for i in range(n_precursors)],
            "species": species,
            "epsilon": rng.normal(0, noise, n_precursors),
            "log_Intensity_mean_A": abundance + [expected_ratio[s] for s in species],
            "log_Intensity_mean_B": abundance,
        }
    )


@pytest.fixture
def intermediates() -> dict:
    """Two workflows' intermediate tables, as the comparison tab passes them in."""
    return {
        "WF_1": make_intermediate(noise=0.2, seed=0),
        "WF_2": make_intermediate(noise=0.5, seed=1),
    }


class TestComparisonLayoutContract:
    """Every generator must declare tabs the web interface can actually render."""

    @pytest.mark.parametrize("generator_class", LFQ_GENERATORS)
    def test_layout_entries_are_well_formed(self, generator_class):
        """Each layout entry carries a name and a title."""
        for config in generator_class().get_comparison_plot_layout():
            assert set(config) >= {"name", "title"}, config
            assert config["name"] and config["title"]

    @pytest.mark.parametrize("generator_class", LFQ_GENERATORS)
    def test_builtin_tabs_come_first(self, generator_class):
        """The two generic tabs are always present, and keep their position."""
        names = [config["name"] for config in generator_class().get_comparison_plot_layout()]
        assert tuple(names[: len(BUILTIN_TAB_NAMES)]) == BUILTIN_TAB_NAMES

    @pytest.mark.parametrize("generator_class", LFQ_GENERATORS)
    def test_every_tab_has_a_description(self, generator_class):
        """A declared tab without a description would render a bare title."""
        generator = generator_class()
        descriptions = generator.get_comparison_plot_descriptions()
        for config in generator.get_comparison_plot_layout():
            assert config["name"] in descriptions, config["name"]

    @pytest.mark.parametrize("generator_class", LFQ_GENERATORS)
    def test_every_declared_plot_is_produced(self, generator_class, intermediates):
        """A name that is neither built in nor produced would show a 'not available' warning."""
        generator = generator_class()
        layout = generator.get_comparison_plot_layout()
        extra = [config["name"] for config in layout if config["name"] not in BUILTIN_TAB_NAMES]
        if not extra:
            return

        figures = generator.generate_comparison_plots(intermediates, precursor_column_name="precursor ion")
        for name in extra:
            assert isinstance(figures.get(name), go.Figure), name

    @pytest.mark.parametrize("generator_class", LFQ_GENERATORS)
    def test_defaults_are_not_shared_between_instances(self, generator_class):
        """Subclasses extend the inherited layout in place, so it must be a fresh object."""
        generator = generator_class()
        generator.get_comparison_plot_layout().append({"name": "scratch", "title": "Scratch"})
        generator.get_comparison_plot_descriptions()["scratch"] = "Scratch"

        assert all(c["name"] != "scratch" for c in generator.get_comparison_plot_layout())
        assert "scratch" not in generator.get_comparison_plot_descriptions()


class TestLowInputGenerator:
    """The low-input generator adds its plot on top of the inherited tabs."""

    def test_inherits_every_hye_plot(self):
        """Low input differs from HYE only in the comparison tab, not the main or in-depth plots."""
        assert issubclass(LFQLowInputPlotGenerator, LFQHYEPlotGenerator)
        assert LFQLowInputPlotGenerator().get_in_depth_plot_layout() == LFQHYEPlotGenerator().get_in_depth_plot_layout()

    def test_extends_rather_than_replaces_the_layout(self):
        """The generic tabs survive, and the accuracy plot is appended after them."""
        base_names = [c["name"] for c in LFQHYEPlotGenerator().get_comparison_plot_layout()]
        names = [c["name"] for c in LFQLowInputPlotGenerator().get_comparison_plot_layout()]

        assert names[: len(base_names)] == base_names
        assert names[len(base_names) :] == ["accuracy_vs_abundance"]

    def test_accuracy_plot_is_inherited_from_hye(self):
        """The figure itself lives on the HYE generator, so any HYE module can opt in."""
        assert "plot_accuracy_vs_abundance" not in LFQLowInputPlotGenerator.__dict__
        assert hasattr(LFQHYEPlotGenerator(), "plot_accuracy_vs_abundance")

    def test_accuracy_plot_degrades_gracefully(self, intermediates):
        """Insufficient or malformed input yields an annotated placeholder, never an exception."""
        generator = LFQLowInputPlotGenerator()

        single = generator.plot_accuracy_vs_abundance({"WF_1": make_intermediate()})
        assert not single.data and "at least two workflows" in single.layout.annotations[0].text

        missing_column = generator.plot_accuracy_vs_abundance(
            {"WF_1": make_intermediate().drop(columns=["epsilon"]), "WF_2": make_intermediate()}
        )
        assert "epsilon" in missing_column.layout.annotations[0].text

        disjoint = dict(intermediates)
        disjoint["WF_2"] = disjoint["WF_2"].assign(**{"precursor ion": lambda df: df["precursor ion"] + "_other"})
        assert "No precursors are shared" in generator.plot_accuracy_vs_abundance(disjoint).layout.annotations[0].text


class TestComparisonTabExtensibility:
    """A module adds a comparison tab from its plot generator alone."""

    def test_a_second_plot_needs_no_web_interface_change(self, intermediates):
        """
        Declaring a second tab is three edits in one class, each plot backed by its own method.

        This mirrors what a future module would write; the web interface resolves tabs purely by
        the ``name`` key, so nothing outside the generator has to know about the new plot.
        """

        class TwoPlotGenerator(LFQLowInputPlotGenerator):
            def get_comparison_plot_layout(self):
                return super().get_comparison_plot_layout() + [{"name": "second_plot", "title": "Second Plot"}]

            def generate_comparison_plots(self, intermediates, precursor_column_name="precursor ion", **kwargs):
                plots = super().generate_comparison_plots(
                    intermediates, precursor_column_name=precursor_column_name, **kwargs
                )
                plots["second_plot"] = self._plot_second(intermediates)
                return plots

            def get_comparison_plot_descriptions(self):
                descriptions = super().get_comparison_plot_descriptions()
                descriptions["second_plot"] = "A second comparison plot."
                return descriptions

            def _plot_second(self, intermediates):
                figure = go.Figure()
                figure.add_bar(x=list(intermediates), y=[len(df) for df in intermediates.values()])
                return figure

        generator = TwoPlotGenerator()
        names = [config["name"] for config in generator.get_comparison_plot_layout()]
        figures = generator.generate_comparison_plots(intermediates, precursor_column_name="precursor ion")
        descriptions = generator.get_comparison_plot_descriptions()

        assert names == list(BUILTIN_TAB_NAMES) + ["accuracy_vs_abundance", "second_plot"]
        for name in ("accuracy_vs_abundance", "second_plot"):
            assert isinstance(figures[name], go.Figure)
            assert descriptions[name]

    def test_an_lfq_module_that_adds_nothing_gets_only_the_generic_tabs(self, intermediates):
        """Inheriting LFQHYEPlotGenerator without overriding anything is a valid, complete module."""
        generator = LFQHYEPlotGenerator()

        assert [c["name"] for c in generator.get_comparison_plot_layout()] == list(BUILTIN_TAB_NAMES)
        assert generator.generate_comparison_plots(intermediates) == {}


class TestComparisonContractScope:
    """The contract belongs to the LFQ family, not to every plot generator."""

    @pytest.mark.parametrize("generator_class", LFQ_GENERATORS)
    def test_lfq_generators_carry_the_contract(self, generator_class):
        """Every LFQ generator can drive the comparison tab."""
        for method in COMPARISON_CONTRACT:
            assert hasattr(generator_class(), method), method

    def test_the_contract_is_rooted_on_the_hye_generator(self):
        """LFQHYEPlotGenerator defines it, so every LFQ generator inherits it from one place."""
        for method in COMPARISON_CONTRACT:
            assert method in LFQHYEPlotGenerator.__dict__, method

    def test_pye_is_part_of_the_lfq_family(self):
        """PYE is HYE with a plasma background, so it inherits rather than duplicates the contract."""
        assert issubclass(LFQPYEPlotGenerator, LFQHYEPlotGenerator)
        for method in COMPARISON_CONTRACT:
            assert method not in LFQPYEPlotGenerator.__dict__, f"{method} should be inherited, not redefined"

    @pytest.mark.parametrize("generator_class", NON_LFQ_GENERATORS + [PlotGeneratorBase])
    def test_non_lfq_generators_do_not_carry_the_contract(self, generator_class):
        """
        De novo and entrapment use a different intermediate schema and never reach the tab.

        Keeping the contract off them means a future module cannot accidentally declare a
        comparison tab the web interface could not populate.
        """
        for method in COMPARISON_CONTRACT:
            assert not hasattr(generator_class, method), method


class TestPrecursorOverlapPlot:
    """The overlap figure is shared by every generator, since every comparison tab shows it."""

    @pytest.mark.parametrize("generator_class", LFQ_GENERATORS)
    def test_counts_shared_and_unique_features(self, generator_class):
        """Bar heights are the set arithmetic of the two feature sets."""
        figure = generator_class().plot_precursor_overlap("WF_1", {"a", "b", "c"}, "WF_2", {"b", "c", "d"})
        counts = {trace.name: int(trace.y[0]) for trace in figure.data}

        assert counts == {"Unique to WF_1": 1, "Shared": 2, "Unique to WF_2": 1}

    def test_handles_disjoint_and_identical_inputs(self):
        """Degenerate overlaps still produce all three bars."""
        generator = LFQHYEPlotGenerator()

        disjoint = {t.name: int(t.y[0]) for t in generator.plot_precursor_overlap("A", {"a"}, "B", {"b"}).data}
        assert disjoint == {"Unique to A": 1, "Shared": 0, "Unique to B": 1}

        identical = {t.name: int(t.y[0]) for t in generator.plot_precursor_overlap("A", {"a"}, "B", {"a"}).data}
        assert identical == {"Unique to A": 0, "Shared": 1, "Unique to B": 0}
