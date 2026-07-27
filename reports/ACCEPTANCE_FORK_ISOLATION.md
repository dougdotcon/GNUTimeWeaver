# Acceptance fork isolation

Branches used frozen distinct suffixes of repeated `A` and `Z` characters.
Both restored the same parent and decoded zero prefix tokens. Their suffixes
were tokenized independently and their continuation hashes diverged at all
tested lengths. The parent state hash remained unchanged.
