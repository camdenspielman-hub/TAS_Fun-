// Analysis driver for the static toolkit's REAL-replay recorder (librm2rec.so, used by static/pfrec.py).
// = the harness driver (tools/harness/driver.cpp, unchanged, included verbatim) + pf_rec.inc (native recorders:
// coverage, write/read sets, value sets, interrupt statistics). Observing hooks only. Needs FCEUX master.
#include "../../harness/driver.cpp"
#include "pf_rec.inc"
