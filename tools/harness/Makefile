# Headless FCEUX core build for Rockman 2 TAS work.
# FCEUX_SRC must point at an FCEUX checkout's src/ directory.
FCEUX_SRC ?= $(error set FCEUX_SRC=/path/to/fceux/src)
OUT       ?= build
CXX       ?= g++
CC        ?= gcc
DEFS      := -DFCEUDEF_DEBUGGER -DHAVE_ASPRINTF -D__LINUX__
CXXFLAGS  += -O2 -fPIC -w -std=gnu++17 $(DEFS) -I$(CURDIR)/shim -I$(FCEUX_SRC) -I$(FCEUX_SRC)/drivers/common -I$(FCEUX_SRC)/drivers
CFLAGS    += -O2 -fPIC -w $(DEFS) -I$(FCEUX_SRC)

CORE_DIRS := $(FCEUX_SRC) $(FCEUX_SRC)/boards $(FCEUX_SRC)/input $(FCEUX_SRC)/utils
EXCLUDE   := lua-engine.cpp backward.cpp
CORE_SRCS := $(filter-out $(addprefix %/,$(EXCLUDE)),$(foreach d,$(CORE_DIRS),$(wildcard $(d)/*.cpp)))
CORE_CSRCS := $(foreach d,$(CORE_DIRS),$(wildcard $(d)/*.c))
CORE_OBJS := $(patsubst $(FCEUX_SRC)/%.cpp,$(OUT)/core/%.o,$(CORE_SRCS)) \
             $(patsubst $(FCEUX_SRC)/%.c,$(OUT)/core/%.c.o,$(CORE_CSRCS))

all: $(OUT)/librm2.so

$(OUT)/core/%.o: $(FCEUX_SRC)/%.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -c $< -o $@

$(OUT)/core/%.c.o: $(FCEUX_SRC)/%.c
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@

$(OUT)/driver.o: driver.cpp
	@mkdir -p $(OUT)
	$(CXX) $(CXXFLAGS) -c $< -o $@

$(OUT)/librm2.so: $(CORE_OBJS) $(OUT)/driver.o
	$(CXX) -shared -o $@ $^ -lz -lpthread

clean:
	rm -rf $(OUT)
