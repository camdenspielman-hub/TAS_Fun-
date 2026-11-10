# Proof kit native build: the headless FCEUX core (via tools/harness) plus the two analysis libraries.
#
#   make -C tools/proof FCEUX_SRC=/path/to/fceux/src OUT=/abs/build/master          # librm2.so librm2pf.so librm2rec.so
#   make -C tools/proof FCEUX_SRC=/path/to/fceux-2.3.0/src OUT=/abs/build/v230 core # librm2.so only (judge core)
#
# FCEUX_SRC must point at an FCEUX checkout's src/ directory. The analysis libraries need FCEUX master: they use
# X6502_MemHook, which FCEUX 2.3.0 does not have. OUT should be an absolute path outside the repository.
# The core objects and librm2.so are built by tools/harness/Makefile with its own flags; the analysis libraries link
# the same core objects with a different driver object. For FCEUX 2.3.0 (recognised by the absence of X6502_MemHook)
# the core is compiled with the 2.3.0 defines of README.md: -DRM2_NO_MEMHOOK -DPSS_STYLE=1 -DLSB_FIRST.
FCEUX_SRC ?= $(error set FCEUX_SRC=/path/to/fceux/src)
OUT       ?= build
CXX       ?= g++
PROOF     := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
HARNESS   := $(abspath $(PROOF)/../harness)
OUTA      := $(abspath $(OUT))
HAS_HOOK  := $(shell grep -q X6502_MemHook $(FCEUX_SRC)/x6502.h && echo 1)
DEFS      := -DFCEUDEF_DEBUGGER -DHAVE_ASPRINTF -D__LINUX__
# FCEUX 2.3.0: no X6502_MemHook; types.h wants PSS_STYLE from the build system (1 = '/' path separator); LSB_FIRST
# selects the little-endian code paths of state.cpp and utils/endian.cpp (same defines as README.md's 2.3.0 build)
OLDDEFS   := $(if $(HAS_HOOK),,DEFS="$(DEFS) -DRM2_NO_MEMHOOK -DPSS_STYLE=1 -DLSB_FIRST")
PFFLAGS   := -O2 -fPIC -w -std=gnu++17 $(DEFS) -I$(HARNESS)/shim -I$(FCEUX_SRC) -I$(FCEUX_SRC)/drivers/common \
             -I$(FCEUX_SRC)/drivers

.PHONY: all core analysis FORCE
all: core analysis
core: $(OUTA)/librm2.so
analysis: $(OUTA)/librm2pf.so $(OUTA)/librm2rec.so

# The core (objects + librm2.so) is delegated to the harness Makefile; it rebuilds nothing when nothing changed.
$(OUTA)/librm2.so: FORCE
	$(MAKE) -C $(HARNESS) FCEUX_SRC=$(FCEUX_SRC) OUT=$(OUTA) $(OLDDEFS)

$(OUTA)/driver_pf.o: $(PROOF)/native/driver_pf.cpp $(PROOF)/native/pf_taint.inc $(HARNESS)/driver.cpp
	@test -n "$(HAS_HOOK)" || { echo "librm2pf.so needs an FCEUX tree with X6502_MemHook (master)"; exit 1; }
	$(CXX) $(PFFLAGS) -c $< -o $@

$(OUTA)/driver_rec.o: $(PROOF)/native/driver_rec.cpp $(PROOF)/native/pf_rec.inc $(HARNESS)/driver.cpp
	@test -n "$(HAS_HOOK)" || { echo "librm2rec.so needs an FCEUX tree with X6502_MemHook (master)"; exit 1; }
	$(CXX) $(PFFLAGS) -c $< -o $@

$(OUTA)/librm2pf.so: $(OUTA)/librm2.so $(OUTA)/driver_pf.o
	$(CXX) -shared -o $@ $$(find $(OUTA)/core -name '*.o' | LC_ALL=C sort) $(OUTA)/driver_pf.o -lz -lpthread

$(OUTA)/librm2rec.so: $(OUTA)/librm2.so $(OUTA)/driver_rec.o
	$(CXX) -shared -o $@ $$(find $(OUTA)/core -name '*.o' | LC_ALL=C sort) $(OUTA)/driver_rec.o -lz -lpthread
