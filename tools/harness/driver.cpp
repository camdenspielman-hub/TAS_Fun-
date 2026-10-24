// Headless FCEUX driver for Rockman 2 TAS work.
//
// Exposes a small C API (used from Python via ctypes and from C++ bots):
// power on, run frames with given pad input, inspect RAM, in-memory
// savestates, and FCEUX's own .fm2 playback for verification.
//
// The emulation core is unmodified FCEUX source; this file only provides the
// FCEUD_* callbacks a frontend must supply, the same way the Qt/Win drivers do.

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdarg>
#include <string>
#include <vector>

#include "types.h"
#include "fceu.h"
#include "driver.h"
#include "state.h"
#include "movie.h"
#include "input.h"
#include "emufile.h"
#include "x6502.h"
#include "file.h"
#include "ppu.h"
#include "palette.h"
#include "debug.h"

extern uint8 *XBuf;
extern char lagFlag;
extern uint32 lagCounter;
extern FCEUGI *GameInfo;
extern int RAMInitOption;
extern X6502 X;

// ---------------------------------------------------------------------------
// Driver callbacks required by the core
// ---------------------------------------------------------------------------
static int g_verbose = 0;

FILE *FCEUD_UTF8fopen(const char *fn, const char *mode) { return fopen(fn, mode); }
EMUFILE_FILE *FCEUD_UTF8_fstream(const char *n, const char *m)
{
	std::string mode = m;
	return new EMUFILE_FILE(n, mode.c_str());
}
FCEUFILE *FCEUD_OpenArchiveIndex(ArchiveScanRecord &, std::string &, int) { return 0; }
FCEUFILE *FCEUD_OpenArchiveIndex(ArchiveScanRecord &, std::string &, int, int *) { return 0; }
FCEUFILE *FCEUD_OpenArchive(ArchiveScanRecord &, std::string &, std::string *) { return 0; }
FCEUFILE *FCEUD_OpenArchive(ArchiveScanRecord &, std::string &, std::string *, int *) { return 0; }
ArchiveScanRecord FCEUD_ScanArchive(std::string) { return ArchiveScanRecord(); }
const char *FCEUD_GetCompilerString() { return "g++ headless"; }
void FCEUD_SetPalette(uint8, uint8, uint8, uint8) {}
void FCEUD_GetPalette(uint8, uint8 *r, uint8 *g, uint8 *b) { *r = *g = *b = 0; }
void FCEUD_PrintError(const char *s) { fprintf(stderr, "[fceux error] %s\n", s); }
void FCEUD_Message(const char *s) { if (g_verbose) fprintf(stderr, "[fceux] %s", s); }
int FCEUD_SendData(void *, uint32) { return 0; }
int FCEUD_RecvData(void *, uint32) { return 0; }
void FCEUD_NetplayText(uint8 *) {}
void FCEUD_NetworkClose(void) {}
void FCEUD_SoundToggle(void) {}
void FCEUD_SoundVolumeAdjust(int) {}
void FCEUD_SaveStateAs(void) {}
void FCEUD_LoadStateFrom(void) {}
void FCEUD_MovieRecordTo(void) {}
void FCEUD_MovieReplayFrom(void) {}
void FCEUD_LuaRunFrom(void) {}
bool FCEUD_ShouldDrawInputAids() { return false; }
void FCEUD_OnCloseGame(void) {}
void FCEUD_AviRecordTo(void) {}
void FCEUD_AviStop(void) {}
bool FCEUI_AviIsRecording(void) { return false; }
bool FCEUI_AviEnableHUDrecording() { return false; }
void FCEUI_SetAviEnableHUDrecording(bool) {}
bool FCEUI_AviDisableMovieMessages() { return true; }
void FCEUI_SetAviDisableMovieMessages(bool) {}
void FCEUI_UseInputPreset(int) {}
void FCEUD_SetEmulationSpeed(int) {}
void FCEUD_TurboOn(void) {}
void FCEUD_TurboOff(void) {}
void FCEUD_TurboToggle(void) {}
int FCEUD_ShowStatusIcon(void) { return 0; }
void FCEUD_ToggleStatusIcon(void) {}
void FCEUD_HideMenuToggle(void) {}
void FCEUD_CmdOpen(void) {}
void FCEUD_DebugBreakpoint(int) {}
void FCEUD_TraceInstruction(uint8 *, int) {}
void FCEUD_FlushTrace() {}
void FCEUD_UpdateNTView(int, bool) {}
void FCEUD_UpdatePPUView(int, int) {}
bool FCEUD_PauseAfterPlayback() { return false; }
void FCEUD_VideoChanged() {}
int FCEUD_NetworkConnect(void) { return 0; }
void FCEUD_GetPalette(uint8, uint8 *, uint8 *, uint8 *, uint8 *) {}
void FCEUI_AviVideoUpdate(const unsigned char *) {}
void FCEUD_StopMovie() {}
bool FCEUD_GetLuaEnable() { return false; }

// Frontend globals the core expects; NTSC defaults, same as FCEUX's own drivers.
int dendy = 0;
int pal_emulation = 0;
bool paldeemphswap = false;
bool swapDuty = false;
bool turbo = false;
int eoptions = 0;
int closeFinishedMovie = 0;
int KillFCEUXonFrame = 0;
uint64 FCEUD_GetTime() { return 0; }
uint64 FCEUD_GetTimeFreq() { return 1000; }
void RefreshThrottleFPS() {}
unsigned int *GetKeyboard(void) { static unsigned int k[256]; return k; }
void GetMouseData(uint32 (&md)[3]) { md[0] = md[1] = md[2] = 0; }
uint32 ModernDeemphColorMap(const uint8 *, const uint8 *, int) { return 0; }

static uint32 g_joy[4];

void FCEUD_SetInput(bool fourscore, bool microphone, ESI port0, ESI port1, ESIFC fcexp)
{
	FCEUI_SetInput(0, SI_GAMEPAD, &g_joy[0], 0);
	FCEUI_SetInput(1, SI_NONE, &g_joy[1], 0);
	FCEUI_SetInputFC(SIFC_NONE, 0, 0);
	FCEUI_SetInputFourscore(false);
}

// ---------------------------------------------------------------------------
// Public C API
// ---------------------------------------------------------------------------
extern "C" {

int rm2_init(const char *rompath, int verbose)
{
	g_verbose = verbose;
	if (!FCEUI_Initialize()) return -1;
	FCEUI_SetVidSystem(0);
	FCEUI_Sound(0);
	if (!FCEUI_LoadGame(rompath, 1, true)) return -2;
	FCEUD_SetInput(false, false, SI_GAMEPAD, SI_NONE, SIFC_NONE);
	return 0;
}

// Equivalent to what FCEUX does before playing a power-on movie:
// RAM init pattern 0 (FCEUX default), battery loading disabled, PowerNES().
void rm2_poweron(void)
{
	extern int disableBatteryLoading;
	RAMInitOption = 0;
	disableBatteryLoading = 1;
	PowerNES();
	disableBatteryLoading = 0;
}

// Run one frame with gamepad byte `pad` (bit0=A,1=B,2=Select,3=Start,
// 4=Up,5=Down,6=Left,7=Right). Returns 1 if the frame was a lag frame.
int rm2_frame(int pad)
{
	uint8 *gfx;
	int32 *sound;
	int32 ssize;
	g_joy[0] = pad & 0xFF;
	FCEUI_Emulate(&gfx, &sound, &ssize, 0);
	return lagFlag ? 1 : 0;
}

uint8 *rm2_ram(void) { return RAM; }
uint8 *rm2_xbuf(void) { return XBuf; }
int rm2_lagcount(void) { return (int)lagCounter; }
int rm2_framecount(void) { return FCEUMOV_GetFrame(); }
int rm2_read(int addr) { return GetMem(addr & 0xFFFF); }
int rm2_pc(void) { return X.PC; }

// In-memory savestates (uncompressed). Returns size written, or -needed.
static EMUFILE_MEMORY g_ms;
int rm2_save(uint8 *buf, int maxlen)
{
	g_ms.truncate(0);
	g_ms.fseek(0, SEEK_SET);
	FCEUSS_SaveMS(&g_ms, 0);
	int len = (int)g_ms.size();
	if (len > maxlen) return -len;
	memcpy(buf, g_ms.buf(), len);
	return len;
}

int rm2_load(const uint8 *buf, int len)
{
	EMUFILE_MEMORY ms((void *)buf, len);
	return FCEUSS_LoadFP(&ms, SSLOADPARAM_NOBACKUP) ? 0 : -1;
}

// Play an .fm2 through FCEUX's movie code exactly as the GUI would.
int rm2_movie_load(const char *path)
{
	return FCEUI_LoadMovie(path, true, 0) ? 0 : -1;
}
int rm2_movie_active(void) { return FCEUMOV_Mode(MOVIEMODE_PLAY | MOVIEMODE_FINISHED) ? 1 : 0; }
int rm2_movie_length(void) { return FCEUI_GetMovieLength(); }
void rm2_movie_stop(void) { FCEUI_StopMovie(); }

// Execution / write hooks for analysis.
typedef void (*hookfn)(unsigned int addr, unsigned int val, void *ud);
void rm2_hook_add(int type, hookfn f) { X6502_MemHook::Add((X6502_MemHook::Type)type, f, nullptr); }
void rm2_hook_remove(int type, hookfn f) { X6502_MemHook::Remove((X6502_MemHook::Type)type, f, nullptr); }

int rm2_reg(int which)
{
	switch (which) {
	case 0: return X.A;
	case 1: return X.X;
	case 2: return X.Y;
	case 3: return X.S;
	case 4: return X.P;
	case 5: return X.PC;
	}
	return 0;
}

// CPU timestamp within the current frame.
int rm2_timestamp(void) { return (int)timestamp; }

} // extern "C"
