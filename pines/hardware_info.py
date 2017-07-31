import platform
import subprocess
import re

def processor_name():
	"""Get a descriptive name of the CPU on this computer"""
	if platform.system() == "Windows":
		result = platform.processor()
	elif platform.system() == "Darwin":
		command =("sysctl", "-n", "machdep.cpu.brand_string")
		result = subprocess.check_output(command).strip()
	elif platform.system() == "Linux":
		command = ("cat", "/proc/cpuinfo")
		all_info = subprocess.check_output(command, shell=True).strip()
		for line in all_info.split("\n"):
			if "model name" in line:
				result = re.sub( ".*model name.*:", "", line,1)
	else:
		result = "unknown system"
	if isinstance(result, bytes):
		return result.decode('UTF-8')
	return result

def node():
	return platform.node()