import sys
import logging
from time import perf_counter
import pandas as pd
from pathlib import Path
from amoor import read_avz, read_key, merge, max_summary

tic = perf_counter()
logging.basicConfig(level=logging.DEBUG,
                    filename='amoor.log',
                    filemode='a',
                    format='%(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')
logging.info('Program started.')

def path_replace(path, old_name, new_name, suffix=None):
    new_path = Path(str(path).replace(str(old_name), str(new_name)))
    if suffix:
        child = new_path.stem + suffix
    else:
        child = new_path.name
    return new_path.parent / child


def file_is_updated(read_path, write_path):
    '''
    Returns True if file at read_path is modified
    more recently than file file at write_path.
    '''
    if write_path.exists():
        # Mod time will be larger for the file that is modified last.
        return read_path.stat().st_mtime < write_path.stat().st_mtime
    else:
        return False


def summary_is_updated(summary_path, sub_paths):
    '''
    Returns True if file at summary_path is modified
    more recently than all files in sub_paths.
    '''
    if summary_path.exists():
        return all([
            summary_path.stat().st_mtime > sub_path.stat().st_mtime
            for sub_path in sub_paths])
    else:
        return False


SOURCE_ROOT = Path('../Resultater')
DEST_ROOT = Path('Output')
MATERIAL_LIB_PATH = Path('amoor/all_materials.csv')
is_nice = True
material_lib = pd.read_csv(MATERIAL_LIB_PATH, index_col='Forkortelse')

pfat_sources = [path for path in SOURCE_ROOT.glob('**/*PFAT.avz')
                if 'max_' not in str(path)]
pfat_dest = [path_replace(path, SOURCE_ROOT, DEST_ROOT, '.csv')
            for path in pfat_sources]
key_sources = list(SOURCE_ROOT.glob('**/*key.txt'))
key_dest = [path_replace(path, SOURCE_ROOT, DEST_ROOT, '.csv')
            for path in key_sources]
merged_dest = [path_replace(pfat_csv, 'PFAT', 'merged')
            for pfat_csv in pfat_dest]
dest_dirs = [path_replace(folder, SOURCE_ROOT, DEST_ROOT)
            for folder in SOURCE_ROOT.glob('**/')
            if str(folder) != str(SOURCE_ROOT)
            if 'max_' not in str(folder)]
DEST_ROOT.mkdir(exist_ok=True)
for folder in dest_dirs:
    folder.mkdir(exist_ok=True)

# Parse PFATs
for pfat_avz in pfat_sources:
    pfat_csv = path_replace(pfat_avz, SOURCE_ROOT, DEST_ROOT, '.csv')
    if file_is_updated(pfat_avz, pfat_csv):
        continue
    pfat_avz_str = str(pfat_avz)
    if 'ulykke' in pfat_avz_str.lower():
        log_txt = pfat_avz_str + ' parsed as accident.'
        logging.info(log_txt)
        print(log_txt)
        df = read_avz.avz_to_df(pfat_avz_str, True, is_nice)
        df.to_csv(pfat_csv)
    else:
        log_txt = pfat_avz_str + ' parsed as intact.'
        logging.info(log_txt)
        print(log_txt)
        df = read_avz.avz_to_df(pfat_avz_str, False, is_nice)
        df.to_csv(pfat_csv)

# Parse key-files
for key_txt in key_sources:
    key_csv = path_replace(key_txt, SOURCE_ROOT, DEST_ROOT, '.csv')
    if file_is_updated(key_txt, key_csv):
        continue
    key_txt_str = str(key_txt)
    log_txt = key_txt_str + ' parsed.'
    logging.info(log_txt)
    print(log_txt)
    df = read_key.key_to_df(key_txt_str)
    df.to_csv(key_csv)

# Merge PFATs og keys
for pfat, key in zip(pfat_dest, key_dest):
    merged = path_replace(pfat, 'PFAT', 'merged')
    if file_is_updated(pfat, merged) and file_is_updated(key, merged):
        continue
    pfat_str = str(pfat)
    key_str = str(key)
    log_txt = 'Merging ' + pfat_str + ' and ' + key_str + '...'
    logging.info(log_txt)
    print(log_txt)
    df = merge.merge(pfat_str, key)
    df.to_csv(merged)

# Make max files
priorities = ['utilization', 'load', 'mbl_bound',
            'min_zload', 'max_zload']
buildup_cols = ['material', 'length', 'utilization']
buildup_segments = ['Bunnkjetting', 'Tau', 'Toppkjetting']
for folder in dest_dirs:
    # Paths
    max_dest = DEST_ROOT / ('-'.join(folder.parts[1:]) + '.xlsx')
    merged_sub_paths = list(folder.glob('**/*merged.csv'))
    # Check mod times
    if summary_is_updated(max_dest, merged_sub_paths):
        continue
    log_txt = 'Making ' + str(max_dest) + '...'
    logging.info(log_txt)
    print(log_txt)
    with pd.ExcelWriter(max_dest) as writer:
        df_max = max_summary.summarize(merged_sub_paths)
        df_max = max_summary.reorder_to_store_order(df_max)  # Reorder columns
        df_max.to_excel(writer, sheet_name='result')
        for priority in priorities:    
            df_util = max_summary.prioritize_components(df_max, priority, 10)
            df_util.to_excel(writer, sheet_name=priority)
        # Right web will be all 0.0 entries for LV results
        if (df_max.right_web != 0).all():
            df_util = max_summary.prioritize_components(df_max,
                                                        'right_web',
                                                        10)
            df_util.to_excel(writer, sheet_name='right_web')
        df_buildup = max_summary.pivot_config(df_max,
                                            buildup_segments,
                                            buildup_cols)
        df_buildup.to_excel(writer, sheet_name='buildup')
        df_materials = material_lib.loc[df_max.material.unique()]
        df_materials.sort_index(inplace=True)
        df_materials.to_excel(writer, sheet_name='materials')
        df_material_matrix = max_summary.material_matrix(df_max)
        df_material_matrix.to_excel(writer, sheet_name='material_matrix')
        df_pluck = max_summary.components_by_material(df_max)
        df_pluck.to_excel(writer, sheet_name='pluck_list')
        df_sources = pd.DataFrame(merged_sub_paths,
                            columns=['source'],
                            index=range(1, len(merged_sub_paths)+1))
        df_sources.to_excel(writer, sheet_name='sources')

print('Done!')
logging.info('Program terminated.')
toc = perf_counter()
logging.info(f'Execution time: {toc-tic:3.1f} s.')