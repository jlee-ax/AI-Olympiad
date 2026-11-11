assert 'sunlight_hours' in plants.columns and 'light_h' not in plants.columns
assert plants.loc[plants.pot_id=='P05','water_ml'].item()==20
assert plants.loc[plants.pot_id=='P05','height_cm'].item()==10
assert new_plants.columns.tolist()==['sample_id','site','light_hours','water_amount_ml','final_height_cm']
print('original data re-created in a separate fresh kernel; not integration plants')
assert site_notes.site.tolist()==['실내','창가']
assert len(new_plants)==4
assert 'joined' not in globals()
print('merge inputs prepared; student groupby/merge/new-key answers remain open')
