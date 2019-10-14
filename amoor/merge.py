import sys
import pandas as pd


def merge(pfat_path, key_path, out_path=None):
	'Inner join *PFAT.csv with *key.csv.'

	# key_path = pfat_path[:-8] + 'key.csv'
	pfat_df = pd.read_csv(pfat_path, index_col="id")
	key_df = pd.read_csv(key_path, index_col="id")
	merged = pd.merge(pfat_df, key_df, left_index=True, right_index=True)
	if out_path:
		merged.to_csv(out_path)
	else:
		return merged


if __name__ == '__main__':
	pfat_path = sys.argv[1]
	key_path = sys.argv[2]
	out_path = sys.argv[3]
	merge(pfat_path, key_path, out_path)