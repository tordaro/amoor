import sys
import pandas as pd
from pathlib import Path


def corresponding_vals(df, target):
    """
    Collect max values, along with corresponding values from other columns,
    in each segment of df with respect to target. Returns a dictionary with
    segment as keys, and a another dictionary containing the values by columns.
    That is, if target='utilization', then max utilization is returned along
    with corresponding entries in other columns, by segment.
    """
    corr_vals = {}
    columns = ["component", "material", "mbl",
               target, "force_lt", "is_accident"]
    for segment in df.segment.unique():
        id_max = df.loc[df.segment==segment, target].idxmax()
        corr_vals[segment] = {col: df[col].iloc[id_max] for col in columns}
    return corr_vals


def speak_vals(df, target, name, unit):
    """
    Wrap corresponding values in df, in natural language. The corresponding
    values are given by max value of target, for each segment. name and unit
    determines the name and unit of the target value in the text, respectively.
    """
    corr_vals = corresponding_vals(df, target)
    df_corr_vals = pd.DataFrame(corr_vals)
    txt_lines = [name.upper() + ":\n"]
    for segment, vals in corr_vals.items():
        txt_lines.append(
            f"Største {name} i {segment.lower()} oppstår i " +
            f"{vals['component']} og er {vals[target]:2.1f} {unit} " +
            f"under lasttilfelle {vals['force_lt']}.\n" +
            f"{segment.capitalize()} i {vals['component']} " +
            f"består av {vals['material']}.\n"
        )
    txt_lines.append(df_corr_vals.to_string())
    txt_lines.append("\n\n")
    return txt_lines


def main():
    """
    Reads directory containing result.xlsx files, and pumps out text summaries
    for each result file.
    """
    dir_path = Path(sys.argv[1])
    result_paths = dir_path.glob("*.xlsx")
    args = (
        ("utilization", "utnyttelse", "%"),
        ("load", "last", "tonn"),
        ("mbl_bound", "MBL-krav", "tonn"),
        ("min_zload", "vertikalkraft", "tonn"),
        ("max_zload", "vertikalkraft", "tonn")
    )
    for result_path in result_paths:
        df_result = pd.read_excel(result_path)
        txt_lines = []
        for arg in args:
            txt_lines += speak_vals(df_result, *arg)
        with open(str(result_path).replace("xlsx", "txt"), "w") as f:
            f.writelines(txt_lines)

if __name__ == '__main__':
    main()