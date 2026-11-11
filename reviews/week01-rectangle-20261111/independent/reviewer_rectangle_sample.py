"""Reviewer-written loop solution of the student instructions, not student work.
Read after initial candidate; teacher example had also been read. This is not a
blind learner result or an actual generic helper supplied in the student notebook.
"""
def reviewer_rectangle_region(grid, coordinates, max_cells):
    (top, left), (bottom, right) = coordinates
    H, W = grid.shape
    if not (0 <= top < bottom <= H and 0 <= left < right <= W):
        raise ValueError("rectangle coordinates violate declared nonempty bounds")
    area = (bottom - top) * (right - left)
    if area > max_cells:
        raise ValueError("rectangle spatial area exceeds declared maximum")
    crop = np.array([[grid[row, col] for col in range(left, right)]
                     for row in range(top, bottom)], dtype=grid.dtype)
    mask = np.zeros((H, W), dtype=bool)
    kept = np.zeros_like(grid)
    for row in range(H):
        for col in range(W):
            selected = top <= row < bottom and left <= col < right
            mask[row, col] = selected
            kept[row, col] = grid[row, col] if selected else 0
    return crop, mask, kept
