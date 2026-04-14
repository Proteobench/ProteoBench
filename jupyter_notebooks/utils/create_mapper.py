import marimo

__generated_with = "0.23.1"
app = marimo.App()


@app.cell
def _():
    from pyteomics import fasta
    import pandas as pd

    return fasta, pd


@app.cell
def _():
    fasta_file_list = [
        "/mnt/d/Proteobench_manuscript_data/ProteoBenchFASTA_DDAQuantification.fasta",
        "/mnt/d/ProteoBench_plasma_raw/HYE_distler.fasta",
    ]
    return (fasta_file_list,)


@app.cell
def _(fasta, fasta_file_list):
    with open(
        "/mnt/c/Users/robbe/Work/ProteoBench/proteobench/io/parsing/io_parse_settings/mapper_new.csv", "w"
    ) as mapper_file:
        mapper_file.write("description,gene_name\n")
        for fasta_path in fasta_file_list:
            fasta_file = fasta.read(fasta_path)
            for entry in fasta_file:
                description = entry.description.split(" ")[0]
                accession = entry.description.split("|")[1]
                print(f"Accession: {accession}, Description: {description}")
                mapper_file.write(f"{description},{accession}\n")
    return


@app.cell
def _(pd):
    mapper = pd.read_csv("/mnt/c/Users/robbe/Work/ProteoBench/proteobench/io/parsing/io_parse_settings/mapper_new.csv")
    return (mapper,)


@app.cell
def _(mapper):
    mapper.drop_duplicates(inplace=True)
    return


@app.cell
def _(mapper):
    mapper.to_csv(
        "/mnt/c/Users/robbe/Work/ProteoBench/proteobench/io/parsing/io_parse_settings/mapper_new.csv", index=False
    )
    return


if __name__ == "__main__":
    app.run()
