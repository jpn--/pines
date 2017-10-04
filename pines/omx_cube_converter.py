print("OMX Batch Maker")

import glob
import argparse
import os
import subprocess

_omx_convert_exe = os.path.join(os.path.abspath(os.path.dirname(__file__)),'omx_convert.exe')


def convert():
	parser = argparse.ArgumentParser()
	parser.add_argument("-r", "--recursive", help="recursively search directories for mat files", action="store_true",
						default=True)
	parser.add_argument("indir", nargs=1, type=str)
	parser.add_argument("outdir", nargs='?', default=None, type=str)
	parser.add_argument("-p", "--pattern", help="pattern to find matrix files", type=str, nargs='?', default='*.mat')
	parser.add_argument("-e", "--executable", help="exe conversion tool path", type=str, nargs='?',
						default=_omx_convert_exe)
	parser.add_argument("-z", "--compress", help="set the compression level", type=int, nargs='?', default=7)
	parser.add_argument("-s", "--chunksize", help="set the chunksize", type=int, nargs='?', default=128000)

	args = parser.parse_args()

	os.chdir(args.indir[0])
	os.environ['PATH'] = os.environ['PATH'] + ";C:\\Program Files\\Citilabs\\CubeVoyager\\;C:\\Program Files (x86)\\Citilabs\\CubeVoyager\\"

	out_dir = args.outdir
	if out_dir is None:
		out_dir = args.indir[0]

	if not os.path.exists(out_dir):
		os.makedirs(out_dir)

	if args.recursive:
		mat_files = glob.iglob(os.path.join('**', args.pattern), recursive=True)
	else:
		mat_files = glob.iglob(args.pattern)

	any_files = False

	for mat_file in mat_files:
		print(mat_file)
		any_files = True
		out_file = os.path.join(out_dir, mat_file)
		out_file_dir = os.path.dirname(out_file)
		if not os.path.exists(out_file_dir):
			os.makedirs(out_file_dir)
		subcall = [args.executable, mat_file, out_file, str(args.compress), str(args.chunksize)]
		try:
			subprocess.call(subcall)
		except:
			print("subprocess:", subcall)
			raise

	if not any_files:
		print("NO FILES FOUND!")
