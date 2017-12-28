import pip, sys, os
from distutils.dir_util import copy_tree

def pip_install(package_names=None, private_repo="camtdm01.camsys.local"):
	if package_names is None:
		if len(sys.argv)>0 and (('pines_pip' in sys.argv[0]) or ('pines-pip' in sys.argv[0])):
			if len(sys.argv)>1 and sys.argv[1]=='install': # ignore install command, it is implied here
				package_names = " ".join(sys.argv[2:])
			else:
				package_names = " ".join(sys.argv[1:])
	try:
		pkgs = package_names.split()
	except AttributeError:
		print("NO PACKAGES GIVEN")
	else:
		for pkg in pkgs:
			result = pip.main(["install", "--upgrade", f'--index-url=http://{private_repo}', f'--trusted-host={private_repo}', pkg])
			if result!=0:
				# failure
				raise ModuleNotFoundError(pkg)

def _pip_install_entry(args=None):
	return pip_install()

def pip_rebuild():
	import libpip2pi.commands
	if len(sys.argv) >= 2:
		local_repo = sys.argv[1]
	else:
		local_repo = "C:\\PythonRepository"
	if len(sys.argv) >= 3:
		private_repo = sys.argv[2]
	else:
		private_repo = r"\\camtdm01\c$\Apache24\htdocs\\"
	libpip2pi.commands.dir2pi(argv=["dir2pi",local_repo, '-S'])
	copy_tree(os.path.join(local_repo, 'simple\\'), private_repo)

def pip_info(package_name):
	from io import StringIO
	import sys
	old_stdout = sys.stdout
	sys.stdout = mystdout = StringIO()
	pip.main(['show',package_name])
	sys.stdout = old_stdout
	return mystdout.getvalue()
