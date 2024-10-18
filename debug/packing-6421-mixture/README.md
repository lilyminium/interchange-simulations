# Investigating 6421

This is a mixture of triethanolamine (490 molecules) and water (510 molecules).

In Barbara's data, the box dimensions had length 59.635 and succeeded.
In the new Evaluator run, the box dimensions had length 57.635 and failed.
In Interchange 0.4.0, the box dimensions had length 55.635. 

Ideally these should all be the same since the box dimensions are computed from mass density.

In an openff-sage environment with Evaluator v0.3.4, the calculated box dimensions were 57.635.

In new Evaluator, they were the same.