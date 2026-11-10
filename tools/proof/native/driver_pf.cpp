// Analysis driver for the certified search and its checkers (librm2pf.so).
// = the harness driver (tools/harness/driver.cpp, unchanged, included verbatim) + pf_taint.inc.
// pf_taint.inc only OBSERVES emulation through registered X6502_MemHook callbacks (taint tracker, read watch,
// write watch); it never changes a register, a memory byte or the timing. A movie input never comes from this library.
// Needs FCEUX master (X6502_MemHook); FCEUX 2.3.0 has no memory hooks.
#include "../../harness/driver.cpp"
#include "pf_taint.inc"
