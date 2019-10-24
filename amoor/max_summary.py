# -*- coding: utf-8 -*-
"""
Created on Wed May 23 08:28:46 2018

@author: tordaronsen
"""
import sys
import re
import pandas as pd
from pathlib import Path
from glob import glob

def reorder_to_store_order(result):
    '''
    Reorder result to match order in master excel file.
    '''
    result_mod = result.reset_index()
    desired_cols = ["name", "id", "force", "force_lt", 
                   "component", "material", "segment", "mbl",
                   "materialcoeff", "max_zforce", "min_zforce",
                   "right_web", "right_web_lt", "conv_norm",
                   "conv_norm_lt","load", "load_limit",
                   "utilization", "max_zload", "min_zload",
                   "mass", "length", "mbl_bound", "mbl_anchor",
                   "mbl_shackle", "mbl_coupling", "edit_id",
                   "force_source", "right_web_source", "conv_norm_source",
                   "max_zload_source", "min_zload_source",
                   "max_zload_lt", "min_zload_lt", "is_accident"]
    allowed_cols = [col for col in desired_cols if col in result_mod.columns]
    return result_mod[allowed_cols]


def _load_results(result_paths):
    'Loads and reference results in a dict.'
    results = {Path().joinpath(*path.parts[1:]):
                pd.read_csv(path, index_col="id") 
                for path in result_paths}
    return results


def add_lt_columns(df_result):
    '''Reads all source columns in df_result, and returns new DF with
    corresponding LT columns added.'''
    df = df_result.copy()
    header_pat = re.compile(r'(\w+)_source')
    entry_pat = re.compile(r'(\d{1,3})merged.csv')
    source_cols = [col for col in df_result.columns if 'source' in col]
    for source_col in source_cols:
        lt_col = header_pat.search(source_col)[1] + "_lt"
        df[lt_col] = df[source_col].apply(
            # entry is Path object without casting
            lambda entry: int(entry_pat.search(str(entry))[1])
        )
    return df


def summarize(result_paths):
    '''Summarizes all results in df_list
    with correct indices, and sources from ref_list.'''

    results = _load_results(result_paths)
    base_ref = list(results.keys())[0]
    df1 = results[base_ref]
    df_final = df1.copy(deep=True)
    # Interdependent columns. Will be updated together. Not sure if right_web
    # should be here. But should be together with conv_norm.
    force_columns = ['force', 'load', 'load_limit', 'right_web',
                    'conv_norm', 'utilization', 'mbl_bound',
                    'mbl_anchor', 'mbl_shackle', 'mbl_coupling',
                    'mbl', 'material', 'length', 'mass', 'materialcoeff',
                    'component', 'is_accident']
    # Reference columns
    source_columns = ['force_source', 'min_zload_source',
                     'max_zload_source', 'conv_norm_source',
                     'right_web_source']
    # Add source columns
    for source in source_columns:
        df_final[source] = base_ref
    
    for ref, df in results.items():
        if ref == base_ref:
            continue
        # Filters
        is_more_utilized = df['utilization'] > df_final['utilization']
        is_bigger_zmin = df['min_zload'] > df_final['min_zload']
        is_bigger_zmax = df['max_zload'] > df_final['max_zload']
        # Update values
        df_final.loc[is_more_utilized, force_columns] = df.loc[is_more_utilized, force_columns]
        df_final.loc[is_bigger_zmax, 'max_zload'] = df.loc[is_bigger_zmax, 'max_zload']
        df_final.loc[is_bigger_zmax, 'max_zforce'] = df.loc[is_bigger_zmax, 'max_zforce']
        df_final.loc[is_bigger_zmin, 'min_zload'] = df.loc[is_bigger_zmin, 'min_zload']
        df_final.loc[is_bigger_zmax, 'min_zforce'] = df.loc[is_bigger_zmax, 'min_zforce']
        # Update sources
        df_final.loc[is_more_utilized, 'force_source'] = ref
        df_final.loc[is_more_utilized, 'conv_norm_source'] = ref
        df_final.loc[is_more_utilized, 'right_web_source'] = ref
        df_final.loc[is_bigger_zmin, 'min_zload_source'] = ref
        df_final.loc[is_bigger_zmax, 'max_zload_source'] = ref
    df_final = add_lt_columns(df_final)
    return df_final


def reorder_and_filter(df_result):
    '''Reorder the columns and exclude
    uninteresting ones.'''
    desired_order = [
        'force_lt', 'component', 'segment', 'material',
        'materialcoeff', 'length', 'mass',
        'mbl', 'mbl_bound', 'load', 'load_limit',
        'utilization', 'min_zload', 'max_zload',
        'right_web', 'conv_norm', 'force_index', 
        'max_zload_index', 'min_zload_index',
        'right_web_index', 'conv_norm_index',
        'min_zload_lt','max_zload_lt',
        'conv_norm_lt', 'right_web_lt',
        'force_source', 'min_zload_source','max_zload_source',
        'conv_norm_source', 'right_web_source', "is_accident"
    ]
    allowed_headers = [name for name in desired_order if name in df_result.columns]
    return df_result[allowed_headers]


def prioritize_components(result_df, by, n_components, segments=slice(None)):
    '''Prioritize n_components components in results_df in segment
    groups by by-argument. Segments of interest are given by segments.
    Convenient for making material configuration table.'''
    ids = result_df.groupby('segment')[by].nlargest(n_components).reset_index().iloc[:,1]
    prioritized = result_df.loc[ids].round(1).set_index(['segment', by])
    return reorder_and_filter(prioritized.loc[segments])


def pivot_config(result_df, segments, columns=['material', 'length'], key_path=None):
    '''Merge result_df and data from key_path, filter results by comp_filter,
    reorder df by components and segments and choose data blocks given by
    column blocks.'''
    segment_filter = (result_df.segment == segments[0])
    for i in range(1, len(segments)):
        segment_filter = segment_filter | (result_df.segment == segments[i])
    
    if key_path:
        key_df = read_key(key_path)
        result_key = pd.merge(result_df, key_df, left_index=True, right_index=True)
        result_slice = result_key.loc[segment_filter]
        return result_slice.pivot(index='component', columns='segment', values=columns)
    else:
        result_slice = result_df.loc[segment_filter]
        return result_slice.pivot(index='component', columns='segment', values=columns)


def material_matrix(result):
    '''
    Pivot result by material and segment.
    Lengts are summed. Components are counted.
    '''
    cols = ["material", "segment", "length", "component"]
    mat_matrix = result[cols]
    mat_matrix.columns = ["Materiale", "Segment", "Total lengde [m]", "Antall komponenter"]
    agg_dict = {"Total lengde [m]": "sum", "Antall komponenter": "count"}
    mat_matrix = mat_matrix.pivot_table(index="Materiale",
                                        columns="Segment",
                                        aggfunc=agg_dict)
    return mat_matrix


def components_by_material(result):
    '''
    Lists components by materials, given materials in result.
    '''
    header = ["Materiale", "Komponent", "Lengder [m]", "Total lengde [m]"]
    mat_comp_list = []
    for material in result.material.unique():
        mat_filter = (result.material == material)
        comp_list = result.loc[mat_filter, "component"].astype(str).tolist()
        len_list = result.loc[mat_filter, "length"].round(1).astype(str).tolist()
        tot_len = result.loc[mat_filter, "length"].sum()
        mat_comp_list.append(
            (material,
            '; '.join(comp_list),
            '; '.join(len_list),
            round(tot_len,1))
        )

    mat_df = pd.DataFrame(mat_comp_list, columns=header)
    mat_df.set_index("Materiale", inplace=True)
    return mat_df