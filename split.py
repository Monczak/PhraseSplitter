import audiosegment
from pydub.silence import split_on_silence
from math import floor

import argparse
import os
import glob
import time

output_format = "wav"
output_sample_rate = 22050
output_sample_width = 2    # 16 bit

audiosegment.converter = "ffmpeg.exe"

parser = argparse.ArgumentParser(description="Split a recording into chunks divided by silence.")
parser.add_argument("-f", "--files", metavar="files", type=str, help="paths to files", nargs="+", required=True)
parser.add_argument("-sl", "--silence-length", metavar="silencelength", type=float, nargs=1, default=600, help="minimum length of silence in between phrases")
parser.add_argument("-st", "--silence-threshold", metavar="silencethreshold", type=float, nargs=1, default=-50, help="anything under this volume (dBFS) will be considered silence")
parser.add_argument("-v", "--verbose", action="store_true")

args = parser.parse_args()


def log(*message, verbose=False):
    if not (verbose and not args.verbose):
        print(*message)


def estimate_processing_time(raw_time):
    return 1.719657E-7 * raw_time ** 2 + 0.0304606672 * raw_time + 0.0044472


def process_file(path):
    split_path = os.path.splitext(path)
    output_dir = "output_{0}".format(split_path[0])

    log("Importing {0}...".format(path))
    sound = audiosegment.from_file(path)

    start_time = time.time()
    log("Estimated processing time:", round(estimate_processing_time(sound.duration_seconds), 2), "seconds")

    log("Resampling to {0} Hz...".format(output_sample_rate), verbose=True)
    resampled_sound = sound.resample(sample_rate_Hz=output_sample_rate, sample_width=output_sample_width)

    log("Splitting...")
    chunks = split_on_silence(resampled_sound, min_silence_len=args.silence_length, silence_thresh=args.silence_threshold)
    log("Split into", len(chunks), "chunks", verbose=True)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    else:
        log("Removing old export files...", verbose=True)
        files = glob.glob(output_dir + "/*")
        for f in files:
            os.remove(f)

    log("Exporting...")

    for i in range(len(chunks)):
        chunks[i].export("{0}/{1}_{2}.{3}".format(output_dir, split_path[0], i, output_format),
                         format=output_format)
        log("Exported {0}/{1} ({2}%)".format(i + 1, len(chunks), floor((i + 1) / len(chunks) * 100)), verbose=True)

    return time.time() - start_time


for path in args.files:
    log("Processing {0} done - took {1} seconds".format(path, round(process_file(path), 2)))

log("Done!")
