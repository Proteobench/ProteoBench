"""
Colour and marker per software tool, shared by the quant (HYE, PYE) and entrapment main plots.

The de novo generator keeps its own ``SOFTWARE_COLORS``/``SOFTWARE_MARKERS`` in
``plot_generator_denovo``, because it plots a different set of tools.
"""

SOFTWARE_COLORS = {
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

SOFTWARE_MARKERS = {
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
