assert feature_cols == ['texture', 'color']
assert model['fill'].statistics_.tolist() == [5.0, 3.0]
assert align_predictions(['X'], [('X', 1)]) == [1]
assert not practice_zip.exists()
print('preflight reviewer oracle passed; existing pipeline only, not the integration candidate')
