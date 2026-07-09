"""Shared plotting constants for ProteoBench."""

# Quant modules (LFQ, entrapment, …)
QUANT_SOFTWARE_COLORS: dict = {
    "MaxQuant": "#88ccef",
    "AlphaPept": "#cc6777",
    "ProlineStudio": "#ddcc77",
    "MSAngel": "#147733",
    "FragPipe": "#342288",
    "i2MassChroQ": "#aa4599",
    "Sage": "#671100",
    "WOMBAT": "#44aa9a",
    "DIA-NN": "#999934",
    "AlphaDIA": "#1D2732",
    "Custom": "#000000",
    "Spectronaut": "#007548",
    "FragPipe (DIA-NN quant)": "#F89008",
    "MSAID": "#bfef45",
    "MetaMorpheus": "#637C7A",
    "Proteome Discoverer": "#911eb4",
    "PEAKS": "#f032e6",
    "quantms": "#f5e830",
}

QUANT_SOFTWARE_MARKERS: dict = {
    "MaxQuant": "circle",
    "AlphaPept": "square",
    "ProlineStudio": "diamond",
    "MSAngel": "cross",
    "FragPipe": "x",
    "i2MassChroQ": "triangle-up",
    "Sage": "triangle-down",
    "WOMBAT": "pentagon",
    "DIA-NN": "star",
    "AlphaDIA": "star-triangle-up",
    "Custom": "star-square",
    "Spectronaut": "diamond-tall",
    "FragPipe (DIA-NN quant)": "circle-x",
    "MSAID": "square-cross",
    "MetaMorpheus": "asterisk",
    "Proteome Discoverer": "hash",
    "PEAKS": "diamond-wide",
    "quantms": "hexagram",
}

# De novo sequencing module
DENOVO_SOFTWARE_COLORS: dict = {
    "AdaNovo": "#88CCEE",
    "Casanovo": "#CC6677",
    "DeepNovo": "#DDCC77",
    "PepNet": "#117733",
    "Pi-HelixNovo": "#332288",
    "Pi-PrimeNovo": "#AA4499",
    "PEAKS": "#661100",
    "SMSNet": "#44AA99",
    "InstaNovo": "#999933",
    "ContraNovo": "#882255",
    "PointNovo": "#E07030",
    "NovoB": "#4477AA",
    "Custom": "#000000",
}

DENOVO_SOFTWARE_MARKERS: dict = {
    "AdaNovo": "circle",
    "Casanovo": "square",
    "DeepNovo": "diamond",
    "PepNet": "cross",
    "Pi-HelixNovo": "x",
    "Pi-PrimeNovo": "triangle-up",
    "PEAKS": "star",
    "SMSNet": "triangle-down",
    "InstaNovo": "pentagon",
    "ContraNovo": "hexagon",
    "PointNovo": "triangle-left",
    "NovoB": "triangle-right",
    "Custom": "circle-open",
}
