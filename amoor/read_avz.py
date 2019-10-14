# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 11:28:46 2019

@author: tordaronsen
"""
import sys
import xml.etree.ElementTree as et
import numpy as np
import pandas as pd
from scipy.constants import g
import zipfile

block_map = {
    'STRESS_LINE_LIST:Local_section_forces.Max_axial_force_[N] {': 'Forces', 
    'STRESS_LINE_LIST:Local_section_forces.Max_axial_force_[N]_INDEX {': 'Force_indices',
    'STRESS_LINE_LIST:Global_section_forces.Max_force_Z_[N] {': 'Z_forces',
    'STRESS_LINE_LIST:Global_section_forces.Max_force_Z_[N]_INDEX {': 'Z_forces_indices',
    'STRESS_LINE_LIST:Nominal_stress_range.Right_web_[MPa] {': 'Right_web',
    'STRESS_LINE_LIST:Nominal_stress_range.Right_web_[MPa]_INDEX {': 'Right_web_indices',
    'STRESS_LINE_LIST:Convergence_norm {': 'Conv_norm',
    'STRESS_LINE_LIST:Convergence_norm_INDEX {': 'Conv_norm_indices'
}


def _model(path, is_accident, is_nice=False, to_clipboard=False):
    '''is_nice is true when names are clever (or nice!). 
    When is_nice=True components are categorized.
    When to_clipboard is true MBL, Materialcoeff and Materials 
    are written to clipboard.'''
    
    if path[-4:] == '.avz':        
        with zipfile.ZipFile(file=path) as zfile:
            with zfile.open('model.xml') as file:
                root = et.XML(file.read().decode('Latin-1'))
    elif path[-4:] == '.xml':
        tree = et.parse('Testmiljø/Horsvaagen_90m_.xml')
        root = tree.getroot()
    else:
        print('Input file must be either .avz or .xml.')
        return None
    
    xml_header = [
    'load_limit', 'edit_id', 'materialcoeff',
    'mbl', 'name', 'component', 'material', 'id'
    ]
    model = {header: [] for header in xml_header}
    for comp in root.iter('component'):
        mcoeff      = float(comp.attrib['materialcoeff'])
        mbl         = float(comp.attrib['breakingload'])/(g*1000)
        name        = comp.attrib['name']
        name_list   = name.split(':')
        model[xml_header[5]].append(name_list[0].strip())   # component
        model[xml_header[6]].append(name_list[-1].strip())  # material
        model[xml_header[4]].append(name)                   # name
        model[xml_header[2]].append(float(comp.attrib['materialcoeff'])) # materialcoeff
        model[xml_header[3]].append(mbl)                    # mbl
        model[xml_header[7]].append(int(comp.attrib['id'])) # id
        model[xml_header[1]].append(int(comp.attrib['number'])) # edit_id
        if is_accident:
            model[xml_header[0]].append(mbl/(mcoeff/1.5))   # load_limit
        else:
            model[xml_header[0]].append(mbl/(mcoeff*1.15))  # load_limit
    
    df_model = pd.DataFrame(data = model)
    df_model.set_index(xml_header[7], inplace=True)
    
    if is_nice:
        df_model[[xml_header[5], 'segment']] = df_model[xml_header[5]].str.split('_', expand=True, n=1)
        df_model.loc[:, 'segment'] = df_model['segment'].astype('category')
    
    return df_model



def _collect_avz_vertices(avz_path):
    '''Parse data from file to a dictionary.'''
    with zipfile.ZipFile(avz_path) as zfile:
        with zfile.open('model.avs') as file:
            is_inside = False
            positions = {"x": [],
                         "y": [],
                         "z": []}
            for line in file:
                nice_line = line.decode('Latin-1').strip()
                if '}' in nice_line and is_inside:
                    return positions

                if is_inside:
                    data_list = nice_line.split()
                    positions["x"].append(np.float64(data_list[2]))
                    positions["y"].append(np.float64(data_list[3]))
                    positions["z"].append(np.float64(data_list[4]))
                
                if "VERTEX_LIST {" == nice_line:
                    is_inside = True
    return positions


def _collect_avz_edges(avz_path):
    with zipfile.ZipFile(avz_path) as zfile:
            with zfile.open('model.avs') as file:
                is_inside = False
                edges = {}
                for line in file:
                    nice_line = line.decode('Latin-1').strip()
                    if "TIMESTEP {" == nice_line:
                        return edges

                    if '}' in nice_line and is_inside:
                        is_inside = False
                    
                    if 'LINE_LIST {' == nice_line:
                        is_inside = True
                        ID = str(next(file).decode('Latin-1').strip().split()[-1])
                        next(file)  # To skip LINE_THICKNESS
                        edges[ID] = []
                    
                    if is_inside:
                        edge_list = nice_line.split()
                        edges[ID].append((np.int32(edge_list[-3]),
                                              np.int32(edge_list[-1])))
    return edges


def _collect_avz_data(avz_path, blocks):
    '''Parse data from file to a dictionary.'''
    with zipfile.ZipFile(avz_path) as zfile:
        with zfile.open('model.avs') as file:
            is_inside = False
            content = []
            data_dicts = {}
            data_key = ''
            for line in file:
                nice_line = line.decode('Latin-1').strip()
                for block_name in blocks:
                    if block_name in nice_line:
                        is_inside = True
                        data_key = block_map[block_name]
                        if data_key not in data_dicts:
                            data_dicts[data_key] = {}

                if '}' in nice_line and is_inside:
                    is_inside = False
                    data_dicts[data_key][content[1]] = [np.float64(text.split()[-1]) for text in content[2:]]
                    content.clear()

                if is_inside:
                    content.append(nice_line)
    return data_dicts


def _avz_result(data_dicts, return_df_data=False):
    '''Make DataFrame from data Dictionary. 
    If return_df_data is true, df_data DataFrame is also returned.'''
    df_data = pd.DataFrame(data_dicts)
    df_data.reset_index(inplace=True)
    df_data.set_index(df_data['index'].str.split(expand=True)[1].astype(np.int64),
                         inplace=True)
    df_data.sort_index(inplace=True)
    # The following approach may not be correct for membrane or beam.
    # The stress blocks has two columns which are (seemingly) equal for truss.
    df_data['Forces_argmax'] = df_data.Forces.apply(np.argmax).astype(np.int64)
    df_data['Z_forces_argmax'] = df_data.Z_forces.apply(np.argmax).astype(np.int64)
    df_data['Z_forces_argmin'] = df_data.Z_forces.apply(np.argmin).astype(np.int64)
    df_data['Right_web_argmax'] = df_data.Right_web.apply(np.argmax).astype(np.int64)
    df_data['Conv_norm_argmax'] = df_data.Conv_norm.apply(np.argmax).astype(np.int64)
    
    df_max = pd.DataFrame(index=df_data.index)
    df_max.index.name = 'id'
    df_max['force'] = df_data.apply(lambda row: row['Forces'][row['Forces_argmax']], axis=1)
    df_max['load'] = df_max['force'] / (g * 1000)
    df_max['max_zforce'] = df_data.apply(lambda row: row['Z_forces'][row['Z_forces_argmax']], axis=1)
    df_max['min_zforce'] = df_data.apply(lambda row: row['Z_forces'][row['Z_forces_argmin']], axis=1)
    df_max['max_zload'] = df_data.apply(lambda row: row['Z_forces'][row['Z_forces_argmax']], axis=1) / (g * 1000)
    df_max['min_zload'] = df_data.apply(lambda row: row['Z_forces'][row['Z_forces_argmin']], axis=1) / (g * 1000)
    df_max['right_web'] = df_data.apply(lambda row: row['Right_web'][row['Right_web_argmax']], axis=1)
    df_max['conv_norm'] = df_data.apply(lambda row: row['Conv_norm'][row['Conv_norm_argmax']], axis=1)
    
    if 'Force_indices' in data_dicts.keys(): # Enough to only check for Force_indices
        df_max['force_index'] = df_data.apply(lambda row: row['Force_indices'][row['Forces_argmax']], axis=1).astype(np.int64)
        df_max['max_zload_index'] = df_data.apply(lambda row: row['Z_forces_indices'][row['Z_forces_argmax']], axis=1).astype(np.int64)
        df_max['min_zload_index'] = df_data.apply(lambda row: row['Z_forces_indices'][row['Z_forces_argmin']], axis=1).astype(np.int64)
        df_max['right_web_index'] = df_data.apply(lambda row: row['Right_web_indices'][row['Right_web_argmax']], axis=1).astype(np.int64)
        df_max['conv_norm_index'] = df_data.apply(lambda row: row['Conv_norm_indices'][row['Conv_norm_argmax']], axis=1).astype(np.int64)
    
    if return_df_data:
        return df_max, df_data
    else:
        return df_max


def avz_to_df(avz_path, is_accident, is_nice=False):
    '''Get a complete DataFrame from .avz-file.'''
    blocks = list(block_map.keys())
    data_dicts = _collect_avz_data(avz_path, blocks)
    df_model = _model(avz_path, is_accident, is_nice)
    df_result = _avz_result(data_dicts)
    df_result['utilization'] = df_result['load'] * 100 / df_model['load_limit']
    if is_accident:
        df_result['mbl_bound'] = df_result['force'] * df_model['materialcoeff'] / (1.5 * g * 1000)
        df_result['mbl_anchor'] = df_result['force'] * (3 / (1.5 * g * 1000))
        df_result['mbl_shackle'] = df_result['force'] * (2 / (1.5 * g * 1000))
        df_result['mbl_coupling'] = df_result['force'] / (g * 1000)
    else:
        df_result['mbl_bound'] = df_result['force'] * df_model['materialcoeff'] * (1.15 / (g * 1000))
        df_result['mbl_anchor'] = df_result['force'] * ((1.15 * 3) / (g * 1000))
        df_result['mbl_shackle'] = df_result['force'] * ((1.15 * 2) / (g * 1000))
        df_result['mbl_coupling'] = df_result['force'] * ((1.15 * 1.5) / (g * 1000))
    return pd.merge(df_model, df_result, left_index=True, right_index=True)


if __name__ == '__main__':
    source_path = sys.argv[1]
    out_path = sys.argv[2]
    if "ulykke" in source_path.lower():
        is_accident = True
        print('Making {} as accident...'.format(out_path))
    else:
        is_accident = False
        print('Making {} as intact...'.format(out_path))
    is_nice = True
    avz_to_df(source_path, is_accident, is_nice).to_csv(out_path)
