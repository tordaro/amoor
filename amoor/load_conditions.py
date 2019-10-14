import sys
import zipfile
import numpy as np
import pandas as pd
import xml.etree.ElementTree as et

def direction(degrees, numeric=True):
    intervals = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]
    if numeric:
        interval_name = [1, 2, 3, 4, 5, 6, 7, 8]
    else:
        interval_name = ['N', 'NØ', 'Ø', 'SØ', 'S', 'SV', 'V', 'NV']
    for i in range(0,len(intervals)-1):
        if intervals[i] <= degrees < intervals[i+1]:
            return interval_name[i+1]
    return interval_name[0]


def _collect_env(avz_path):
    '''Read environment data from .avz-file and return
    it in a dictionary.'''
    with zipfile.ZipFile(avz_path) as zfile:
        with zfile.open('model.xml') as file:
            root = et.XML(file.read().decode('Latin-1'))

    current_keys = ['strom5', 'strom5retn', 'strom15', 'strom15retn']
    load_keys = root[0][0].keys() + current_keys
    keys_to_numeric = ['waveamplitude', 'waveperiod', 'waveangle',
                       'wavetype', 'currentx', 'currenty', 'windx', 'windy']
    env_data = {key: [] for key in load_keys}

    for load in root[0]:
        current1 = load[0][0]
        current2 = load[0][1]
        for key in keys_to_numeric:
            env_data[key].append(float(load.attrib[key]))
        env_data['group'].append(int(load.attrib['group']))
        env_data['type'].append(load.attrib['type'])
        env_data['strom5'].append(float(current1.attrib['velocity']))
        env_data['strom5retn'].append(float(current1.attrib['direction']))
        env_data['strom15'].append(float(current2.attrib['velocity']))
        env_data['strom15retn'].append(float(current2.attrib['direction']))
    return pd.DataFrame(env_data)


def read_env_data(avz_path):
    '''Organize environment data from .avz-file
    and return it in a DataFrame.'''
    df_env = _collect_env(avz_path)
    df_env.type = pd.Categorical(df_env.type)
    df_env.index += 1
    df_env['hs'] = df_env.waveamplitude * 1.05  # For some reason
    df_env['tp'] = df_env.waveperiod
    df_env['vind'] = np.sqrt(df_env.windx ** 2 + df_env.windy ** 2)
    df_env['vindretn'] = (np.arctan2(df_env.windx, df_env.windy)
                              * 180 / np.pi + 180)
    df_env['sektor'] = df_env.vindretn.apply(lambda r: direction(r, numeric=False))
    df_env['num_sector'] = df_env.vindretn.apply(lambda r: direction(r, numeric=True))
    df_env['type'] = pd.Categorical(df_env['type'])
    return df_env[['sektor', 'hs', 'tp', 'vind', 'vindretn',
                   'strom5', 'strom5retn', 'strom15', 'strom5retn',
                  'type', 'group', 'num_sector', 'waveangle']]


if __name__ == '__main__':
    avz_path = sys.argv[1]
    out_path = sys.argv[2]
    env = read_env_data(avz_path)
    env.to_excel(out_path)