import ast,json
expected=[[6,12],[5,3],[3,9]]
actual=(X_new@W_new).tolist()
print(json.dumps({'scope':'provided_setup_and_reviewer_reference_for_blank_A','expected':expected,'actual':actual,'answer_blank':not ast.parse(_review_candidate_cell_sources[29]).body}))
assert actual==expected and not ast.parse(_review_candidate_cell_sources[29]).body
