def rectangle_region(grid, coordinates, max_cells):
    (top, left), (bottom, right) = coordinates
    H, W = grid.shape
    if not (0 <= top < bottom <= H and 0 <= left < right <= W):
        raise ValueError("비어 있거나 격자 밖인 영역입니다")
    area = (bottom - top) * (right - left)
    if area > max_cells:
        raise ValueError("남길 수 있는 칸 수를 넘었습니다")
    crop = grid[top:bottom, left:right].copy()
    mask = np.zeros((H, W), dtype=bool)
    mask[top:bottom, left:right] = True
    kept = np.zeros_like(grid)
    kept[top:bottom, left:right] = crop
    return crop, mask, kept
