assert 'sunlight_hours' in plants.columns and 'light_h' not in plants.columns
assert plants.loc[plants.pot_id=='P05','water_ml'].item()==20
assert plants.loc[plants.pot_id=='P05','height_cm'].item()==10
assert new_plants.columns.tolist()==['sample_id','site','light_hours','water_amount_ml','final_height_cm']
print('original data re-created in a separate fresh kernel; not integration plants')
assert np.isclose(lengths.var(ddof=0),8/3)
assert pd.Series(lengths).var(ddof=0)==lengths.var(ddof=0)
assert pd.Series(lengths).var(ddof=1)!=lengths.var(ddof=0)
