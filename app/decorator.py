# Author: Marek Jankech
# Copyright Marek Jankech 2022 Released under the MIT license

def singleton(cls):
	"""
	Can be used as a decorator for classes.
	Ensures only one instance will be created for the class.
	"""

	instance = None

	def getinstance(*args, **kwargs):
		nonlocal instance
		if instance is None:
			instance = cls(*args, **kwargs)
		return instance

	return getinstance