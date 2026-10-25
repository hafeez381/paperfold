# `python3 -m adr` was PaperFold's command; TextFold's is `python3 -m textfold`, which this runs with the same arguments
import runpy
import sys

print("PaperFold is now TextFold: python3 -m textfold " + " ".join(sys.argv[1:]), file=sys.stderr)
runpy.run_module("textfold", run_name="__main__", alter_sys=True)
