import sys
import pandas as pd
from pathlib import Path

root = sys.argv[1]
paths = Path(root).glob("**/*merged.csv")
results = [(path, pd.read_csv(path)) for path in paths]
control_path, control_result = results[0]
control_cols = [
        "name",
        "id",
        "material",
        "segment",
        "mbl",
        "materialcoeff"
]

print("Control result from: ", control_path)
with pd.ExcelWriter("compare_results.xlsx") as writer:
    control_result[control_cols].to_excel(writer,
            sheet_name="control_"+control_path.stem)
    for path, result in results:
        is_equal = result[control_cols].equals(control_result[control_cols])
        print(path, is_equal)
        if not is_equal:
            result[control_cols].to_excel(writer, sheet_name=path.stem)

