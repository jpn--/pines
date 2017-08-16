import pip, sys


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
			result = pip.main(["install", "--upgrade", f'--index-url=http://{private_repo}', pkg])
			if result!=0:
				# failure
				raise ModuleNotFoundError(pkg)

def _pip_install_entry(args=None):
	return pip_install()

