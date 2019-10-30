"""
Read formatted CSV and produce load conditions
"""

import sys
import pandas as pd
from util import *
from scipy.constants import pi, g


def make_env_AP(path, decimal=b',', sep='\t', col_names=None):
    '''Reads Akvaplan-niva environmental data from 
    .csv-file, without headers, and returns it in 
    properly formatted DataFrame.'''
    AP_env = pd.read_csv(path, decimal=decimal, sep=sep, header=None)
    if not col_names:
        col_names = ['retning_strom',
                     '_målt_5', '_strom_5_10', '_strom_5_50',
                     'justert_5_10', 'justert_5_50',
                     '_målt_15', '_strom_15_10', '_strom_15_50',
                     'justert_15_10', 'justert_15_50',
                     'retning_vind',
                     'vind_10', 'vind_50',
                     'Hs_10', 'Tp_10',
                     'Hs_50', 'Tp_50']
    AP_env.columns = col_names

    AP_env["himmelretning"] = AP_env["retning_vind"].apply(direction)
    AP_env["sektor"] = AP_env["retning_vind"].apply(lambda r: direction(r, numeric=False))
    idx_df = AP_env.groupby("himmelretning").idxmax()

    env105050 = pd.DataFrame({
        "sektor": AP_env["sektor"][idx_df["Hs_10"]].values,
        "hs": AP_env["Hs_10"][idx_df["Hs_10"]].values,
        "tp": AP_env["Tp_10"][idx_df["Hs_10"]].values,
        "vind": AP_env["vind_10"][idx_df["Hs_10"]].values,
        "vindretn": AP_env["retning_vind"][idx_df["Hs_10"]].values,
        "strom5": AP_env["justert_5_50"][idx_df["justert_5_50"]].values / 100,
        "strom5retn": AP_env["retning_strom"][idx_df["justert_5_50"]].values,
        "strom15": AP_env["justert_15_50"][idx_df["justert_15_50"]].values / 100,
        "strom15retn": AP_env["retning_strom"][idx_df["justert_15_50"]].values
    })

    env501010 = pd.DataFrame({
        "sektor": AP_env["sektor"][idx_df["Hs_50"]].values,
        "hs": AP_env["Hs_50"][idx_df["Hs_50"]].values,
        "tp": AP_env["Tp_50"][idx_df["Hs_50"]].values,
        "vind": AP_env["vind_50"][idx_df["Hs_50"]].values,
        "vindretn": AP_env["retning_vind"][idx_df["Hs_50"]].values,
        "strom5": AP_env["justert_5_10"][idx_df["justert_5_10"]].values / 100,
        "strom5retn": AP_env["retning_strom"][idx_df["justert_5_10"]].values,
        "strom15": AP_env["justert_15_10"][idx_df["justert_15_10"]].values / 100,
        "strom15retn": AP_env["retning_strom"][idx_df["justert_15_10"]].values
    })

    if "Hs_10_hav" in AP_env:
        idx_df_hav = idx_df.dropna()

        env105050_hav = pd.DataFrame({
            "sektor": AP_env["sektor"][idx_df_hav["Hs_10_hav"]].values,
            "hs": AP_env["Hs_10_hav"][idx_df_hav["Hs_10_hav"]].values,
            "tp": AP_env["Tp_10_hav"][idx_df_hav["Hs_10_hav"]].values,
            "vind": AP_env["vind_10"][idx_df_hav["Hs_10_hav"]].values,
            "vindretn": AP_env["retning_vind"][idx_df_hav["Hs_50_hav"]].values,
            "strom5": AP_env["justert_5_50"][idx_df_hav["justert_5_50"]].values / 100,
            "strom5retn": AP_env["retning_strom"][idx_df_hav["justert_5_50"]].values,
            "strom15": AP_env["justert_15_50"][idx_df_hav["justert_15_50"]].values / 100,
            "strom15retn": AP_env["retning_strom"][idx_df_hav["justert_15_50"]].values
        })

        env501010_hav = pd.DataFrame({
            "sektor": AP_env["sektor"][idx_df_hav["Hs_50_hav"]].values,
            "hs": AP_env["Hs_50_hav"][idx_df_hav["Hs_50_hav"]].values,
            "tp": AP_env["Tp_50_hav"][idx_df_hav["Hs_50_hav"]].values,
            "vind": AP_env["vind_50"][idx_df_hav["Hs_50_hav"]].values,
            "vindretn": AP_env["retning_vind"][idx_df_hav["Hs_50_hav"]].values,
            "strom5": AP_env["justert_5_10"][idx_df_hav["justert_5_10"]].values / 100,
            "strom5retn": AP_env["retning_strom"][idx_df_hav["justert_5_10"]].values,
            "strom15": AP_env["justert_15_10"][idx_df_hav["justert_15_10"]].values / 100,
            "strom15retn": AP_env["retning_strom"][idx_df_hav["justert_15_10"]].values
        })

        env105050_hav.index += env501010.index[-1] + 1
        env501010_hav.index += env105050_hav.index[-1] + 1
        env501010 = pd.concat([env501010, env105050_hav, env501010_hav])

    env105050.index += 1
    env501010.index += 9
    env_final = pd.concat([env105050, env501010])
    env_final["steilhet"] = (env_final["tp"]**2 / env_final["hs"]) * (g / (1.9 * 2 * pi))
    return env_final

if __name__ == '__main__':
    lr_csv_path = sys.argv[1]
    load_conditions = make_env_AP(lr_csv_path)
    print(load_conditions)
    load_conditions.to_excel("miljo.xlsx")