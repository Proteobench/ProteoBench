import marimo

__generated_with = "0.23.1"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns

    return pd, plt, sns


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### This notebook shows how to create figures from ProteoBench intermediate files.
    #### As an example, we will plot the intensity vs. the logFC, similar to Fig3d in the publication of the benchmark data for Ion Quantification (Van Puyvelde et al, 2022)
    """)
    return


@app.cell
def _(pd):
    # read in ProteoBench intermediate file
    intermediate_file = pd.read_csv("../../test/data/intermediate_files/result_performance_MaxQuant_20241216_120952.csv")

    # take mean of log intensity mean a and log intensity mean b
    intermediate_file["logIntensityMean"] = (
        intermediate_file["log_Intensity_mean_A"] + intermediate_file["log_Intensity_mean_B"]
    ) / 2

    intermediate_file
    return (intermediate_file,)


@app.cell
def _(intermediate_file, plt, sns):
    # plot FC vs Intensity per species
    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        data=intermediate_file,
        y="logIntensityMean",
        x="log2_A_vs_B",
        hue="species",
        palette=dict(YEAST="#FE3E3E", HUMAN="#4CA64C", ECOLI="#4C4CFF"),
        s=10
    )
    plt.title("log2FC vs logIntensityMean")
    plt.xlabel("log2_FC(A:B)")
    plt.ylabel("log2_Intensity_Mean")
    plt.legend(title="Organism")

    # add verical lines at log2FC = 0 (human), log2FC = 1 (Yeast), logFC = -2 (Ecoli)
    plt.axvline(x=0, color="green", linestyle="--", label="log2FC = 0")
    plt.axvline(x=1, color="red", linestyle="--", label="log2FC = 1")
    plt.axvline(x=-2, color="blue", linestyle="--", label="log2FC = -2")
    return


if __name__ == "__main__":
    app.run()
