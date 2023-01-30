# https://aur.archlinux.org/packages/scc-bin <- the software used here
echo lexutils/models:
scc lexutils/models
echo lexutils/helpers:
scc lexutils/helpers
echo tests:
scc tests
#echo "all python files:"
#scc *.py
echo "Total:"
scc \
--exclude-dir .mypy_cache \
--exclude-dir .pytest_cache \
--exclude-dir lib \
--exclude-dir venv \
 -M ".*\.csv"
