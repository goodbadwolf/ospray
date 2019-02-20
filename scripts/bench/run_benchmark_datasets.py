#!/usr/bin/python
## ======================================================================== ##
## Copyright 2016-2019 Intel Corporation                                    ##
##                                                                          ##
## Licensed under the Apache License, Version 2.0 (the "License");          ##
## you may not use this file except in compliance with the License.         ##
## You may obtain a copy of the License at                                  ##
##                                                                          ##
##     http://www.apache.org/licenses/LICENSE-2.0                           ##
##                                                                          ##
## Unless required by applicable law or agreed to in writing, software      ##
## distributed under the License is distributed on an "AS IS" BASIS,        ##
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. ##
## See the License for the specific language governing permissions and      ##
## limitations under the License.                                           ##
## ======================================================================== ##

import argparse
import os
import subprocess
import re
import csv
import sys
import math

# Various constants
CSV_FIELD_NAMES = ["test name", "max", "min", "median", "median abs dev",
                   "mean", "std dev", "no. of samples"]
DEFAULT_IMG_WIDTH = 1024
DEFAULT_IMG_HEIGHT = 1024
DEFAULT_IMG_DIR = "bench_output"
EXE_NAME = "ospBenchmark"
RESULTS_RE = re.compile(r'.*(Statistics.*)', re.DOTALL)
FLOAT_RE = re.compile(r'-?\d+(?:\.\d+)?')
ERROR_RE = re.compile(r'.*(?:#ospsg: FATAL )([^\n\r]*).*', re.DOTALL)
SCORE_DIFF_PERCENT = 15.0
MAX_DIFF_PER_PIXEL = 0
TEST_PARAMETERS = {
    "fiu1": ("test_data/fiu-groundwater.xml", "-vp 500.804565 277.327850 -529.199829 "
        "-vu 0.000000 1.000000 0.000000 -vi 21.162066 -62.059830 -559.833313", ""),
    "fiu2": ("test_data/fiu-groundwater.xml", "-vp -29.490566 80.756294 -526.728516 "
        "-vu 0.000000 1.000000 0.000000 -vi 21.111689 12.973234 -443.164886", ""),

    "heptane1": ("test_data/csafe-heptane-302-volume.osp",
        "-vp 286.899994 422.800018 -30.200012 -vu 0 1 0 -vi 151.000000 151.000000 151.000000", ""),
    "heptane2": ("test_data/csafe-heptane-302-volume.osp",
        "-vp -36.2362 86.8541 230.026 -vu 0 0 1 -vi 150.5 150.5 150.5", ""),

    "llnl_iso1": ("test_data/llnl-2048-iso.xml", "-vp 3371.659912 210.557999 -443.156006 "
        "-vu -0.000000 -0.000000 -1.000000 -vi 1439.359985 1005.450012 871.119019", ""),
    "llnl_iso2": ("test_data/llnl-2048-iso.xml", "-vp 2056.597168 999.748108 402.587219 "
        "-vu -0.000000 -0.000000 -1.000000 -vi 1439.358887 1005.449951 871.118164", ""),

    "magnetic1": ("test_data/magnetic-512-volume.osp",
        "-vp 255.5 -1072.12 255.5 -vu 0 0 1 -vi 255.5 255.5 255.5", ""),
    "magnetic2": ("test_data/magnetic-512-volume.osp",
        "-vp 431.923 -99.5843 408.068 -vu 0 0 1 -vi 255.5 255.5 255.5", ""),
    "magnetic3": ("test_data/magnetic-512-volume.osp",
        "-vp 431.923 -99.5843 408.068 -vu 0 0 1 -vi 255.5 255.5 255.5", ""),

    "sponza1": ("test_data/crytek-sponza/sponza.obj", "-vp 667.492554 186.974228 76.008301 ",
        "-vu 0.000000 1.000000 0.000000 -vi 84.557503 188.199417 -38.148270"),

    "san_miguel1": ("test_data/san-miguel/sanMiguel.obj", "-vp -2.198506 3.497189 23.826025 ",
        "-vu 0.000000 1.000000 0.000000 -vi -2.241950 2.781175 21.689358"),

    "sibenik1": ("test_data/sibenik/sibenik.obj", "-vp -17.734447 -13.788272 3.443677 ",
        "-vu 0.000000 1.000000 0.000000 -vi -2.789550 -10.993323 0.331822"),
}

# Takes a string "xxx" and prints "=== xxx ==="
def print_headline(line):
    print "=== {} ===".format(line.strip())

# Unless an optimization to the algorithm is made, the score achieved in benchmark should be
# consistent across builds. This function compares results of current test with recorded ones.
def check_score_correctness(stats, baseline_score, test_name):
    if test_name not in baseline_score:
        return True, None

    frame_score = float(stats[4])
    target_score = baseline_score[test_name]

    if frame_score == 0 or target_score == 0:
        if abs(frame_score - target_score) > 1:
            return False, "the difference between the expected and actual score is too high"
        else:
            return True, None

    ratio = frame_score / target_score

    if ratio > (1.0 + SCORE_DIFF_PERCENT / 100.0) or ratio < (1.0 - SCORE_DIFF_PERCENT / 100.0):
        error_msg = "the difference between the expected and actual score is too high " \
            "({:.2f} ratio)".format(ratio)
        return False, error_msg

    return True, None

# Reads expecteded benchmark results from a given file
def get_baseline_score(filename):
    baseline_score = {}

    baseline = open(args.baseline, "r")
    reader = csv.reader(baseline, delimiter=',')
    for row in [r for r in reader][1:]:
        baseline_score[row[0]] = float(row[5])

    return baseline_score

# Load an image generated by ospBenchmark (does not read ANY ppm file)
def read_ppm(filename):
    file = open(filename, "rb")

    file.readline()
    [width, height] = [ int(s) for s in file.readline().strip().split() ]
    file.readline()

    bytes = file.read()[:(3 * width*height)]

    return bytes

# Compares two given images, blurring them beforehand to reduce the impact of noise
def compare_images(img, ref_img):
    if not os.path.isfile(ref_img) or not os.path.isfile(img):
        return True

    img1 = read_ppm(img)
    img2 = read_ppm(ref_img)

    if len(img1) != len(img2):
        return False

    for (p1, p2) in zip(img1, img2):
      if abs(ord(p1) - ord(p2)) > MAX_DIFF_PER_PIXEL:
        return False

    return True

# Prints names of all tests
def print_tests_list():
    for test_name in sorted(TEST_PARAMETERS):
        print test_name

# Runs a test and returns its exit code, stdout and stderr
def run_single_test(test_name, exe, img_dir, use_scivis):
    filename, camera, params = TEST_PARAMETERS[test_name]
    results = []

    command_sv = "{} {} {} -bf 100 -wf 50 -r sv" \
        " -i {}/test_{}_scivis {}" \
        .format(exe, filename, camera, img_dir, test_name, params)

    command_pt = "{} {} {} -bf 100 -wf 50 -r pt" \
        " -i {}/test_{}_pt {}".format(exe,filename, camera, img_dir, test_name, params)

    command = command_sv if use_scivis else command_pt

    print "Running \"{}\"".format(command.strip())

    child = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    test_output = child.communicate()
    test_retcode = child.returncode

    return test_retcode, test_output

# Checks if return code, stdandard output and generated images are correct
def analyze_results(test_name, retcode, output, output_csv, img_dir, baseline_score, args):
    if retcode != 0:
        return False, "subprocess returned with exit code {}".format(retcode)

    stdout = output[0]
    stderr = output[1]

    fatal_error = ERROR_RE.match(stderr)
    if fatal_error:
        return False, "fatal error: {}".format(fatal_error.group(1))

    results = RESULTS_RE.match(stdout)
    print results.group(1).strip()

    stats = re.findall(FLOAT_RE, results.group(1))

    if output_csv:
        output_csv.writerow([test_name] + stats)

    score_correct, err_msg = check_score_correctness(stats, baseline_score, test_name)
    if not score_correct:
        return False, err_msg

    if args.reference:
        img = "{}/test_{}.ppm".format(img_dir, test_name)
        ref_img = "{}/test_{}.ppm".format(args.reference, test_name)

        if not compare_images(img, ref_img):
            return False, "reference image differs from the generated one"

    return True, None

def run_tests(args):
    output_csv = None
    if args.output:
        out_file = open(args.output, "w+")
        output_csv = csv.writer(out_file, delimiter=',')
        output_csv.writerow(CSV_FIELD_NAMES)

    baseline_score = {} if not args.baseline else get_baseline_score(args.baseline)
    bench_img_width = DEFAULT_IMG_WIDTH if not args.width else args.width
    bench_img_height = DEFAULT_IMG_HEIGHT if not args.height else args.height
    tests_to_run = set(args.tests.split(',')) if args.tests else set(TEST_PARAMETERS)

    use_sv_options = [False] if args.renderer == "pt" else \
        [True] if args.renderer == "scivis" else [True, False]
    tests_to_run = set([(name, sv) for name in tests_to_run for sv in use_sv_options])

    exe = "./{} -w {} -h {}".format(EXE_NAME, bench_img_width, bench_img_height)
    img_dir = DEFAULT_IMG_DIR

    print "All tests run at {} x {}".format(bench_img_width, bench_img_height)

    # Create images directory
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)

    failed_tests = 0

    for test_num, (test_name, use_scivis) in enumerate(sorted(tests_to_run)):
        test_name_full = "{} ({})".format(test_name, "scivis" if use_scivis else "pt")
        test_name_full2 = "{}_{}".format(test_name, "scivis" if use_scivis else "pt")
        print_headline("TEST {}/{}: {}".format(test_num + 1, len(tests_to_run), test_name_full))

        retcode, output = run_single_test(test_name, exe, img_dir, use_scivis)
        passed, error_msg = analyze_results(test_name_full2, retcode, output, output_csv, img_dir,
                                            baseline_score, args)

        if passed:
            print_headline("PASSED")
        else:
            print_headline("FAILED, {}".format(error_msg))
            failed_tests += 1

    sys.exit(failed_tests)

# Command line arguments parsing
parser = argparse.ArgumentParser()
parser.add_argument("--width", help="width of the image, default {}".format(DEFAULT_IMG_WIDTH),
                    type=int)
parser.add_argument("--height", help="height of the image, default {}".format(DEFAULT_IMG_HEIGHT),
                    type=int)
parser.add_argument("--tests",
                    help="takes comma-separated list of tests to run; if not specified, all tests "
                    "are run")
parser.add_argument("--tests-list", help="print list of all tests", action="store_true")
parser.add_argument("--output", help="output file name")
parser.add_argument("--baseline",
                    help="results of previous benchmark that will serve as a reference")
parser.add_argument("--reference", help="path to directory with reference images")
parser.add_argument("--renderer", help="type of renderer used",
                    choices=["both", "scivis", "pt"], default="both")
args = parser.parse_args()

if args.tests_list:
    print_tests_list()
else:
    run_tests(args)

