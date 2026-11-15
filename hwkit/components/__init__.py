"""Models of purchased components that more than one build uses.

Each module reads its dimensions from the current build's part folder with
``spec`` (the part must exist in that build), so a component model is shared
while each build keeps its own evidence-tagged part.toml.
"""
