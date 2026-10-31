"""Deterministic Science of Reading analysis engine.

This package holds the logic that makes claims about text, so every
result can be traced back to explicit data:

- ``gpc``            Grapheme-phoneme correspondence (GPC) catalog.
- ``scope_sequence`` Default phonics scope & sequence, plus custom-scope loading.
- ``decoder``        Word- and passage-level decodability analysis, aligning each
                     word's spelling to its dictionary pronunciation (CMU
                     Pronouncing Dictionary) using only GPCs that have been taught.
- ``cueing``         Detection of three-cueing (MSV) prompting language.
"""
