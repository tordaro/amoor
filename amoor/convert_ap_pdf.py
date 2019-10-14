"""
Convert Akvaplan Niva PDF to csv.
"""

import sys
from tabula import convert_into

if __name__ == '__main__':
	lr_path = sys.argv[1]
	page = sys.argv[2]
	convert_into(input_path=lr_path,
                output_path="lr_unformatted.csv",
                output_format="tsv",
                encoding="CP1252",
                pages=page,
                lattice=True)