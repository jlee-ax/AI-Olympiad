# Primary-document reading note: NumPy matmul
URL: https://numpy.org/doc/stable/reference/generated/numpy.matmul.html
Version: v2.5, accessed 2026-11-11. Actual browser read: signature, exceptions and 2D notes/examples.
This is an operator paraphrase, not an original-source copy or authenticated document.
For two 2D inputs, a shared contraction dimension is summed. Shapes (n,d) and (d,m) produce (n,m). A mismatching shared dimension raises an error. For this probe, the library contract supports comparing each query row against each gallery row after transpose. It says nothing about semantic correctness of arbitrary feature order or gallery IDs. Those are explicit task and data contracts.
