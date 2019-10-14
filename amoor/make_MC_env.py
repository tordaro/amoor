import sys
import pandas as pd
import numpy as np
from util import *
from scipy.constants import pi, g

def _init_mc_current():
    '''Return initialized dictionary.
    Ready to be loaded with data.'''
    mc_current = {
        "strom5": np.zeros(16),
        "strom5retn": np.zeros(16),
        "strom15": np.zeros(16),
        "strom15retn": np.zeros(16)
    }
    return mc_current
    

def _load_mc_current(path, depth, data_dict):
    '''Load given initialized data_dict at 
    given depth.'''
    with open(path, "rb") as file:
        for i, line in enumerate(file):
            nice_list = line.decode("CP1252").split()

            data_dict["strom{}".format(depth)][(i+4) % 8] = float(nice_list[-1])
            data_dict["strom{}retn".format(depth)][(i+4) % 8] = float(nice_list[1])

            data_dict["strom{}".format(depth)][(i+4) % 8 + 8] = float(nice_list[-2])
            data_dict["strom{}retn".format(depth)][(i+4) % 8 + 8] = float(nice_list[1])


def _read_mc_waves(path):
    '''Read MultiConsult wave data and
    return it in properly formatted dictionary,
    ready to be DataFramed.'''
    mc_wave_data = {}
    with open(path, "rb") as file:
        for line in file:
            nice_list = line.decode("CP1252").split()
            mc_wave_data[nice_list[0]] = [float(val) for val in nice_list[1:]]

    mc_waves = {
        "sektor": np.array([direction(val, False) 
            for val in mc_wave_data["retning_vind_10"] + mc_wave_data["retning_vind_10"]]),
        "hs": np.array(mc_wave_data["Hs_10"] + mc_wave_data["Hs_50"]),
        "tp": np.array(mc_wave_data["Tp_10"] + mc_wave_data["Tp_50"]),
        "vind": np.array(mc_wave_data["vind_10"] + mc_wave_data["vind_50"]),
        "vindretn": np.array(mc_wave_data["retning_vind_10"] + mc_wave_data["retning_vind_50"])
    }
    return mc_waves


def _read_mc_ocean_waves(path, env_df):
    '''Read ocean MultiConsult ocean wave data
    and return DataFrame slice that can be merged
    with env_df.'''
    mc_ocean_data = {}
    with open(path, "rb") as file:
        for line in file:
            nice_list = line.decode("CP1252").split()
            mc_ocean_data[nice_list[0]] = [float(val) for val in nice_list[1:]]
    
    lt = ([int(val) for val in mc_ocean_data["lt_10"]]
          + [int(val) for val in mc_ocean_data["lt_50"]])
    mc_ocean_waves = {
        "hs": np.array(mc_ocean_data["Hs_10"] + mc_ocean_data["Hs_50"]),
        "tp": np.array(mc_ocean_data["Tp_10"] + mc_ocean_data["Tp_50"])
    }
    
    ocean_df = env_df.loc[lt].copy()
    ocean_df.loc[:, "hs"] = mc_ocean_waves["hs"]
    ocean_df.loc[:, "tp"] = mc_ocean_waves["tp"]
    ocean_df.reset_index(inplace=True, drop=True)
    ocean_df.index += env_df.index[-1] + 1
    return ocean_df


def make_env_mc(waves_path, current_path_1, current_path_2, current_depths=[5,15], ocean_path=None):
    '''Make complete environmental DataFrame from MultiConsult
    data. Must have 3-4 input text files, in a standard format.'''
    mc_waves = _read_mc_waves(waves_path)
    
    mc_current = _init_mc_current()
    _load_mc_current(current_path_1, current_depths[0], mc_current)
    _load_mc_current(current_path_2, current_depths[1], mc_current)
    
    env_final = pd.DataFrame({**mc_waves, **mc_current})
    env_final.index += 1
    env_final["steilhet"] = (env_final["tp"]**2 / env_final["hs"]) * (g / (1.9 * 2 * pi))
    
    if ocean_path:
        ocean_env = _read_mc_ocean_waves(ocean_path, env_final)
        ocean_env["steilhet"] = (ocean_env["tp"]**2 / ocean_env["hs"]) * (g / (1.9 * 2 * pi))
        return pd.concat([env_final, ocean_env])
    else:
        return env_final


if __name__ == '__main__':
    args = sys.argv[1:]
    env = make_env_mc(*args)
    print(env)
    env.to_excel("miljo.xlsx")