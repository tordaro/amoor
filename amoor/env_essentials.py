"""Environment summary printer
Takes *.xlsx file with formatted environment and stores summary text
to file where "xlsx" is replaced with "txt. Useful for reports.
"""

import sys
import pandas as pd
from util import *


def get_corr_vals(df, target, corr_vals):
    """
    Takes environment df along with corr_vals dictionary, that is filled with
    max values of target, and corresponding directions. Nothing is returned
    but corr_vals is filled inplace.
    """ 
    corr_vals[target] = {}
    max_val = df[target].max()
    idx = (df[target] == max_val)
    sektor = df.loc[idx, "sektor"].unique().tolist()
    strom5retn = df.loc[idx, "strom5retn"].apply(
        lambda r: direction((r+180)%360, False)).unique().tolist()
    strom15retn = df.loc[idx, "strom15retn"].apply(
        lambda r: direction((r+180)%360, False)).unique().tolist()

    corr_vals[target]["max_val"] = max_val
    corr_vals[target]["sektor"] = "; ".join(sektor)
    corr_vals[target]["strom5retn"] = "; ".join(strom5retn)
    corr_vals[target]["strom15retn"] = "; ".join(strom15retn)


def collect_corr_vals(df):
    """
    Takes environment df and returns a dictionary with max value of targets,
    hard coded below, and corresponding directions.
    """
    corr_vals = {}
    targets = ("vind", "hs", "strom5", "strom15")
    for target in targets:
        get_corr_vals(df, target, corr_vals)
    return corr_vals


def speak_vals(df):
    """
    Wraps all the key values in natural language and returnes a suitable
    string that can be stored to file.
    """
    corr_vals = collect_corr_vals(df)
    summary_txt = (
        f"Største vindhastighet er {corr_vals['vind']['max_val']} m/s " +
        f"og kommer fra {corr_vals['vind']['sektor']}. Største " +
        f"bølge er {corr_vals['hs']['max_val']} m og kommer fra " +
        f"{corr_vals['hs']['sektor']}. Største " +
        f"strømhastighet på 5 m dyp er {corr_vals['strom5']['max_val']} m/s " +
        f"og kommer fra {corr_vals['strom5']['strom5retn']}. Største " +
        f"strømhastighet på 15 m dyp er {corr_vals['strom15']['max_val']} " +
        f"m/s og kommer fra {corr_vals['strom15']['strom5retn']}." 
    )
    return summary_txt


def main():
    path = sys.argv[1]
    output = path.replace("xlsx", "txt")
    df = pd.read_excel(path)
    summary_txt = speak_vals(df)
    with open(output, 'w') as f:
        f.write(summary_txt)

if __name__ == '__main__':
    main()