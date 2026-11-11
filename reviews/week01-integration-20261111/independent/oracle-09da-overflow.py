import math
value = observed_mean([1e308, 1e308])
print('All input values are finite; exact mean is 1e308; returned:', value)
assert math.isfinite(value), '09da contract violation: finite inputs produce infinite mean'
