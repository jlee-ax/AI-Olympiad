assert 'sunlight_hours' in plants.columns and 'light_h' not in plants.columns
assert plants.loc[plants.pot_id=='P05','water_ml'].item()==20
assert plants.loc[plants.pot_id=='P05','height_cm'].item()==10
assert new_plants.columns.tolist()==['sample_id','site','light_hours','water_amount_ml','final_height_cm']
print('original data re-created in a separate fresh kernel; not integration plants')
assert two_by_three.shape==(2,3) and grid.shape==(3,2)
assert 'task_array' not in globals()
print('student reshape/broadcast answers remain unfilled')
