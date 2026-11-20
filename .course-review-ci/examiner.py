"""Make new examiner cases inside one runner. The seed, numeric cases and keys stay in temporary storage."""
from collections import Counter
from itertools import combinations
from random import SystemRandom

rng = SystemRandom()


def design():
    target, other, different = rng.sample(range(10, 900), 3)
    def probe(entrypoint, spec, examples, oracle, tolerance=None):
        cases = []
        for index, (kind, item) in enumerate(examples):
            row = {"id": f"case-{index+1}", "kind": kind, "input": item, "expected": oracle(item)}
            if kind in {"invariant", "sensitive"}:
                row["base"] = "case-1"
            if tolerance is not None:
                row["atol"] = tolerance
            cases.append(row)
        return {"entrypoint": entrypoint, "spec": spec, "cases": cases}

    matrix = [[target, 1], [target, 8], [other, 1], [target, 1]]
    labels = [0, 6, 6, 0]
    def vectors(rows, classes, columns):
        return {"features": rows, "labels": classes, "keep": columns}
    def ambiguity(case):
        rows, classes, cols = (case[k] for k in ("features", "labels", "keep"))
        return [[i, j] for i,j in combinations(range(len(rows)), 2) if classes[i] != classes[j]
                and all(rows[i][k] == rows[j][k] for k in cols)]
    vector_cases=[
        ("normal", vectors(matrix, labels, [0])),
        ("invariant", vectors([[x+different,y] for x,y in matrix],labels,[0])),
        ("sensitive", vectors(matrix,labels,[0,1])),
        ("boundary", vectors(matrix,labels,[])),
        ("boundary", vectors([],[],[])),
        ("boundary", vectors([[target]], [0], [0])),
    ]

    ids = ["im-"+str(v) for v in (target,other,different)]
    source = [[ids[0],0],[ids[1],6]]
    asks = [ids[0],ids[1],ids[0].upper(),ids[0]]
    def lookup(rows, names):
        return {"records":rows,"requests":names}
    def labels_for(case):
        data = case["records"]
        return [next((v for name,v in data if name==q), None) for q in case["requests"]]
    lookup_cases=[
        ("normal",lookup(source,asks)),
        ("invariant",lookup(list(reversed(source)),asks)),
        ("sensitive",lookup([[ids[0],7],source[1]],asks)),
        ("boundary",lookup(source,[])),
        ("boundary",lookup([], [ids[2]])),
    ]

    names = ["p"+str(target),"p"+str(other),"unused"]
    values=[[target,None,None],[0,other,None],[different,other,None]]
    def frame(rows,keep):
        return {"columns":names, "values":rows, "keep":keep}
    def column_means(case):
        columns = {name: [row[j] for row in case["values"] if row[j] is not None]
                   for j,name in enumerate(case["columns"])}
        counts=[]; means=[]
        for key in case["keep"]:
            data=columns[key];counts.append(len(data));means.append(sum(data)/len(data) if data else None)
        return {"shape":[len(case["values"]),len(counts)],"observed":counts,"means":means}
    chosen=[names[2],names[0],names[1]]
    mean_cases=[
        ("normal",frame(values,chosen)),
        ("invariant",frame(values[::-1],chosen)),
        ("sensitive",frame([[target+19,None,None],values[1],values[2]],chosen)),
        ("boundary",frame([],chosen)),
        ("boundary",frame(values,[])),
        ("boundary",frame([[None,None,None]],names[:1])),
    ]

    groups=rng.sample(range(1,20),3); first,second,absent=groups
    rows=[[first,target],[second,other],[second,target],[second,target],[first,other]]
    def chart(data,keys,unit,library):
        return {"groups":keys,"rows":data,"target":target,"unit":unit,"library":library}
    def frequency(case):
        totals=Counter(g for g,_ in case["rows"])
        counts=Counter(g for g,x in case["rows"] if x==case["target"])
        heights=[counts[g] if case["unit"]=="count" else 100*counts[g]/totals[g] for g in case["groups"]]
        return {"groups":case["groups"],"heights":heights}
    chart_cases=[
        ("normal",chart(rows,[second,first],"percent","matplotlib")),
        ("invariant",chart(rows[::-1],[second,first],"percent","seaborn")),
        ("sensitive",chart([*rows,[second,other]],[second,first],"percent","matplotlib")),
        ("boundary",chart(rows,groups,"count","seaborn")),
        ("boundary",chart([],groups,"count","matplotlib")),
        ("boundary",chart([[second,target]],[second],"percent","seaborn")),
        ("boundary",chart([[first,other]],[first],"percent","matplotlib")),
    ]
    return {"probes":{
        "transfer":probe("indistinguishable_pairs","Find all lexicographically ordered positions i<j with different numeric labels and equal selected integer coordinates; an empty projection compares empty tuples.",vector_cases,ambiguity),
        "KOAI-01.practical":probe("restore_digit_predictions","From distinct, case-sensitive record names return the prediction or null for each requested name in request order, retaining zero and duplicates.",lookup_cases,labels_for),
        "KOAI-02.practical":probe("named_feature_means","For the requested named columns in order return shape, number observed and mean over non-null entries. A column with no observations has a null mean.",mean_cases,column_means,1e-8),
        "KOAI-03.practical":probe("plot_pixel_frequency","Make the designated library's bar plot for the requested groups and return groups and heights. Count mode includes unobserved groups; percent divides by the within-group observation count, which is positive in percentage inputs.",chart_cases,frequency,1e-8)}}
