import sys
import pandas as pd
from scipy.constants import g


def key_to_df(key_path):
    '''Reads relevant data from key.txt-file.
    mass_w   ==> effective mass in water [kg]
    mass     ==> mass [kg]
    bouyancy ==> bouyancy [kg]
    length   ==> length [m]'''
    with open(key_path, 'r') as file:
        header = ['id', 'mass_w', 'mass', 'boyancy', 'length']
        lines = {name: [] for name in header}
        for line in file:
            if ' Mass centre beams and trusses ' in line:
                # To stop after first block is read
                break
            if 'Component' in line:
                data = line.split()
                if len(data) == 6:
                    lines[header[0]].append(int(data[1]))
                    lines[header[-1]].append(float(data[-1]))
                    for i in range(1, len(header)-1):
                        lines[header[i]].append(float(data[i+1])/g)
    df_key = pd.DataFrame(lines)
    df_key.set_index('id', inplace=True)
    return df_key


if __name__ == '__main__':
    source_path = sys.argv[1]
    out_path = sys.argv[2]
    key_to_df(source_path).to_csv(out_path)
