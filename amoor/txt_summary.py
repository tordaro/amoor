#!/home/Tordaro/anaconda3/bin/python

import sys
import numpy as np
import pandas as pd

def key_vals(key_values,
             df,
             arg_col,
             id_col,
             segments=None,
             key_ext="",
             lower_bound=None):
    
    if segments:
        seg_filter = np.array([False] * len(df))
        for segment in segments:
            seg_filter = (seg_filter | (df.segment == segment))
        df = df.loc[seg_filter]
    if lower_bound:
        cond_val_filter = (df[arg_col] >= lower_bound)
        cond_vals = df.loc[cond_val_filter, arg_col].round(1).astype(str).tolist()
        cond_ids = df.loc[cond_val_filter, id_col].unique().astype(str).tolist()
        key_values[arg_col+key_ext] = '; '.join(cond_vals)
        key_values[arg_col+key_ext+"_id"] = '; '.join(cond_ids)
    else:
        max_val = df[arg_col].max()
        max_val_filter = (df[arg_col] == max_val)
        max_ids = df.loc[max_val_filter, id_col].unique().astype(str).tolist()
        key_values[arg_col+key_ext] = max_val
        key_values[arg_col+key_ext+"_id"] = '; '.join(max_ids)

if __name__ == '__main__':
    eq_path = sys.argv[1]
    intact_path = sys.argv[2]
    acc_path = sys.argv[3]
    both_path = sys.argv[4]
    env_path = sys.argv[5]
    lv = pd.read_excel(eq_path, sheet_name="result")
    ml = pd.read_excel(intact_path, sheet_name="result")
    acc_ml = pd.read_excel(acc_path, sheet_name="result")
    final = pd.read_excel(both_path, sheet_name="result")
    env = pd.read_excel(env_path)
    max_val_args = [
    #     df, arg_max_col, id_col, segment, key_ext, lower_bound
        (env, "vind", "sektor"),
        (env, "strom5", "sektor"),
        (env, "strom15", "sektor"),
        (env, "hs", "sektor"),
        (lv, "load", "component", ["Tau"], "_lv_tau_intakt"),
        (lv, "load", "component", ["Ramme"], "_lv_ramme_intakt"),
        (lv, "load", "component", ["Hanefot"], "_lv_hane_intakt"),
        (ml, "load", "component", ["Tau"], "_ml_tau_intakt"),
        (ml, "load", "component", ["Ramme"], "_ml_ramme_intakt"),
        (ml, "load", "component", ["Hanefot"], "_ml_hane_intakt"),
        (ml, "max_zload", "component", ["Hanefot"], "_ml_hane_intakt"),
        (ml, "min_zload", "component", ["Bunnkjetting"], "_ml_bunnkj_intakt", 4),
        (ml, "load", "component", ["Tau"], "_ml_ramme_intakt"),
        (acc_ml, "load", "component", ["Tau"], "_ml_tau_ulykke"),
        (acc_ml, "load", "component", ["Ramme"], "_ml_ramme_ulykke"),
        (acc_ml, "load", "component", ["Hanefot"], "_ml_hane_ulykke"),
        (acc_ml, "min_zload", "component", ["Bunnkjetting"], "_ml_bunnkj_ulykke", 4),
        (acc_ml, "max_zload", "component", ["Hanefot"], "_ml_hane_ulykke"),
        (final, "mbl_bound", "component", ["Tau"], "_final_tau"),
        (final, "mbl_bound", "component", ["Ramme"], "_final_ramme"),
        (final, "mbl_bound", "component", ["Hanefot"], "_final_hane"),
        (final, "mbl_coupling", "component", ["Ramme", "Tau"], "_final_ramme_tau"),
        (final, "mbl_anchor", "component", ["Tau"], "_final_tau"),
        (final, "min_zload", "component", ["Bunnkjetting"], "_ml_bunnkj", 4),
        (final, "utilization", "component")
    ]

    key_data = {}
    for arg in max_val_args:
        key_vals(key_data, *arg)

    with open("amoor/summary_template.txt", "r") as file:
        content = file.read()

    with open("summary_formatted.txt", "w") as file:
        file.write(content.format(**key_data))
