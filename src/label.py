"""
Usage:
python label.py \
    --scope phm2012 \
    --thresholds -3.5 3.0 0.05 \
    --src-breakpoint "..\build\meta\phm2012\anomaly-detection-unequal\breakpoint.csv"
"""
import os
import glob
import numpy as np
import pandas as pd
from bisect import bisect_left
from utils.utils import log, prepare_directory, get_args, get_chunk_count
from utils.preprocess import get_datetime

def main():
    args = get_args()
    src_dir = os.path.join(
        '../build/data', args.scope, 'initialized'
    )
    dest_dir = prepare_directory(os.path.join(
        '../build/data', args.scope, 'labeled'
    ))
    filenames = glob.glob(os.path.join(
        src_dir, '*.csv'
    ))
    threshold_step = args.thresholds[2]
    thresholds = np.arange(args.thresholds[0], args.thresholds[1], threshold_step)
    df_breakpoints = pd.read_csv(args.src_breakpoint)
    for filename in filenames:
        log('parsing %s in scope %s' % (os.path.basename(filename), args.scope))

        first_datetime, last_datetime, chunk_count = get_datetime(filename)
        total_seconds = (last_datetime - first_datetime).total_seconds()

        df_chunks = pd.read_csv(
            filename,
            chunksize=args.chunk_size
        )

        for chunk_idx, df_chunk in enumerate(df_chunks):
            header = chunk_idx is 0
            mode = 'a' if chunk_idx > 0 else 'w'

            df_chunk['datetime'] = pd.to_datetime(df_chunk['datetime'],  infer_datetime_format=True)

            log('parsing chunk %d/%d' % (chunk_idx, chunk_count))

            df_chunk['rul'] = (last_datetime -  df_chunk['datetime']).astype('timedelta64[us]') / 1000000
            df_chunk['rulp'] = df_chunk['rul'] / total_seconds
            df_chunk['level_x'] = [bisect_left(thresholds, element) for element in df_chunk['x']]
            df_chunk['level_y'] = [bisect_left(thresholds, element) for element in df_chunk['y']]
            df_chunk['symbol_x'] = [bisect_left(df_breakpoints['x'], element) for element in df_chunk['x']]
            df_chunk['symbol_y'] = [bisect_left(df_breakpoints['y'], element) for element in df_chunk['y']]

            df_chunk.to_csv(
                os.path.join(
                    dest_dir,
                    os.path.basename(filename)
                ),
                mode=mode,
                header=header,
                index=False
            )

main()
