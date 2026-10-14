"""Replay the reader's pure PSI/artifact regressions against revision two.

This imports definitions only; it never starts javac, the parser JVM, or a
runtime-closure check. Native API initialization still requires the new run.
"""
import importlib.util
from pathlib import Path
import unittest


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


original = load('original_kotlin_reader_tests', 'test_kotlin_loc.py')
original.loc = load('kotlin_reader_v2', 'kotlin_loc_v2.py')
PsiTests = original.PsiTests
ArtifactTests = original.ArtifactTests


if __name__ == '__main__':
    unittest.main()
