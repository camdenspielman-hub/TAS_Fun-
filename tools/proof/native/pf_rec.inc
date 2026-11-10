
// ---------------------------------------------------------------------------
// pf_static ANALYSIS additions (proof/static).  Never used to make movie material.
// Native recorders, no Python callbacks:
//   * coverage: for every executed instruction start (PRG offset), the set of PRG banks mapped at $8000
//   * execution outside PRG ROM (PC < $8000) is flagged per PC
//   * writes: distinct (instruction, address) pairs, where "instruction" is the PRG offset of the executing
//     instruction, or INT for the 3 pushes of an NMI/IRQ entry (detected by the vector fetch read)
//   * reads of $0000-$7FFF: distinct (instruction, address) pairs
//   * value sets: every value written to each RAM byte $0000-$07FF
//   * NMI statistics: interrupted PC (+bank) histogram, min stack pointer, NMI duration, NMI spacing
// ---------------------------------------------------------------------------
#include "cart.h"
#include <unordered_map>
extern uint64 timestampbase;
#ifndef RM2_NO_MEMHOOK
static const uint64_t PF_INT_ID = 0xFFFFF;       // pseudo instruction id for interrupt-entry pushes
static inline long pf_romoff(unsigned a) {
	if (a < 0x8000) return -1;
	uint8 *p = Page[a >> 11] + a;
	long off = (long)(p - PRGptr[0]);
	if (off >= 0 && off < (long)PRGsize[0]) return off;
	return -1;
}
static inline int pf_mbank(void) { long o = pf_romoff(0x8000); return o < 0 ? -1 : (int)(o / 0x4000); }
static uint16_t pf_cov[512 * 1024];
static uint8_t *pf_regs = nullptr;           // per PRG offset: 3 x 32-byte bitsets (A, X, Y values at the boundary)
static uint8_t pf_ramexec[0x10000];
struct PfPend { uint32 addr; uint8 val; };
static std::vector<PfPend> pf_pend;
static std::vector<int> pf_vecpos;
static long pf_cur_off = -2; static unsigned pf_cur_pc = 0; static uint8 pf_cur_op = 0xEA;
static std::unordered_map<uint64_t, int> pf_wset, pf_rset;
static uint8_t pf_vals[0x800][32];
static int pf_on = 0, pf_rd_on = 0;
static int pf_minS = 0x1FF;
static uint32_t pf_intpc[0x10000];          // interrupted PC histogram (NMI/IRQ entries): the instruction that ran last
static std::unordered_map<uint32_t, uint32_t> pf_intret;  // (return PC << 8 | mapped bank) -> count: exact boundary
static uint64_t pf_nmi_t0 = 0, pf_nmi_last = 0; static int pf_in_nmi = 0;
static uint64_t pf_nmi_maxdur = 0, pf_nmi_mingap = ~0ULL, pf_nmi_count = 0, pf_nmi_nested = 0;
static unsigned pf_nmi_entry = 0xCFED, pf_rti_pc = 0xD0D3;

static inline uint64_t pf_instr_id(void) {
	if (pf_cur_off >= 0) return (uint64_t)pf_cur_off;
	return 0x80000ULL + (pf_cur_pc & 0xFFFF);
}
static void pf_flush(void) {
	size_t n = pf_pend.size();
	if (n == 0 && pf_vecpos.empty()) return;
	char isint[64]; memset(isint, 0, sizeof(isint));
	bool first = true;
	for (int p : pf_vecpos) {
		bool brk = first && pf_cur_op == 0x00;
		first = false;
		if (!brk) for (int k = p - 3; k < p; k++) if (k >= 0 && k < 64) isint[k] = 1;
	}
	uint64_t id0 = pf_instr_id();
	for (size_t i = 0; i < n; i++) {
		uint64_t id = (i < 64 && isint[i]) ? PF_INT_ID : id0;
		uint64_t key = (id << 16) | (pf_pend[i].addr & 0xFFFF);
		if (pf_wset.find(key) == pf_wset.end()) pf_wset[key] = g_frameno;
	}
	pf_pend.clear(); pf_vecpos.clear();
}
static void pf_exec_hook(unsigned int addr, unsigned int, void *)
{
	if (!pf_on) return;
	pf_flush();
	long off = pf_romoff(addr);
	int mb = pf_mbank();
	pf_cur_off = off; pf_cur_pc = addr;
	if (off >= 0) {
		pf_cov[off] |= (uint16_t)(1u << (mb & 15)); pf_cur_op = PRGptr[0][off];
		if (pf_regs) {
			uint8_t *r = pf_regs + (size_t)off * 96;
			r[X.A >> 3] |= (uint8_t)(1u << (X.A & 7));
			r[32 + (X.X >> 3)] |= (uint8_t)(1u << (X.X & 7));
			r[64 + (X.Y >> 3)] |= (uint8_t)(1u << (X.Y & 7));
		}
	}
	else { pf_ramexec[addr & 0xFFFF] = 1; pf_cur_op = (addr < 0x2000) ? RAM[addr & 0x7FF] : 0xEA; }
	if ((int)X.S + 0x100 < pf_minS) pf_minS = (int)X.S + 0x100;
	if (addr == pf_nmi_entry) {
		uint64_t t = timestampbase + timestamp;
		if (pf_in_nmi) pf_nmi_nested++;
		if (pf_nmi_count) { uint64_t g = t - pf_nmi_t0; if (g < pf_nmi_mingap) pf_nmi_mingap = g; }
		pf_nmi_t0 = t; pf_in_nmi = 1; pf_nmi_count++;
	}
	if (addr == pf_rti_pc && pf_in_nmi) {
		uint64_t d = timestampbase + timestamp - pf_nmi_t0;
		if (d > pf_nmi_maxdur) pf_nmi_maxdur = d;
		pf_in_nmi = 0;
	}
}
static void pf_write_hook(unsigned int addr, unsigned int val, void *)
{
	if (!pf_on) return;
	PfPend p; p.addr = addr & 0xFFFF; p.val = val & 0xFF;
	pf_pend.push_back(p);
	if (addr < 0x2000) { unsigned a = addr & 0x7FF; pf_vals[a][(val & 0xFF) >> 3] |= (uint8_t)(1u << (val & 7)); }
}
static void pf_read_hook(unsigned int addr, unsigned int, void *)
{
	if (!pf_on) return;
	if (addr == 0xFFFA || addr == 0xFFFE) {
		// vector fetch: the 3 writes just before it are the pushes of BRK or of an interrupt entry
		pf_vecpos.push_back((int)pf_pend.size());
		bool brk = pf_vecpos.size() == 1 && pf_cur_op == 0x00;
		if (!brk) {
			pf_intpc[pf_cur_pc & 0xFFFF]++;
			// X.PC still holds the interrupted PC here (the vector is assigned after this read returns)
			uint32_t k = ((uint32_t)(X.PC & 0xFFFF) << 8) | (uint32_t)(pf_mbank() & 0xFF);
			pf_intret[k]++;
		}
		return;
	}
	if (!pf_rd_on || addr >= 0x8000) return;
	uint64_t key = (pf_instr_id() << 16) | (addr & 0xFFFF);
	if (pf_rset.find(key) == pf_rset.end()) pf_rset[key] = g_frameno;
}
extern "C" {
void pf_start(int reads)
{
	pf_on = 1; pf_rd_on = reads;
	X6502_MemHook::Add(X6502_MemHook::Exec, pf_exec_hook, nullptr);
	X6502_MemHook::Add(X6502_MemHook::Write, pf_write_hook, nullptr);
	X6502_MemHook::Add(X6502_MemHook::Read, pf_read_hook, nullptr);
}
void pf_stop(void)
{
	pf_flush();
	pf_on = 0;
	X6502_MemHook::Remove(X6502_MemHook::Exec, pf_exec_hook, nullptr);
	X6502_MemHook::Remove(X6502_MemHook::Write, pf_write_hook, nullptr);
	X6502_MemHook::Remove(X6502_MemHook::Read, pf_read_hook, nullptr);
}
int pf_prgsize(void) { return (int)PRGsize[0]; }
void pf_regs_enable(void) { if (!pf_regs) pf_regs = (uint8_t *)calloc((size_t)PRGsize[0] * 96, 1); }
void pf_regs_get(uint8_t *out) { if (pf_regs) memcpy(out, pf_regs, (size_t)PRGsize[0] * 96); }
int pf_mapped_bank(void) { return pf_mbank(); }
void pf_cov_get(uint16_t *out, int n) { int m = (int)PRGsize[0]; if (n < m) m = n; memcpy(out, pf_cov, m * 2); }
void pf_ramexec_get(uint8_t *out) { memcpy(out, pf_ramexec, 0x10000); }
void pf_vals_get(uint8_t *out) { memcpy(out, pf_vals, sizeof(pf_vals)); }
void pf_intpc_get(uint32_t *out) { memcpy(out, pf_intpc, sizeof(pf_intpc)); }
int pf_wcount(void) { return (int)pf_wset.size(); }
int pf_intret_count(void) { return (int)pf_intret.size(); }
void pf_intret_dump(uint32_t *out) { size_t i = 0; for (auto &kv : pf_intret) { out[i++] = kv.first; out[i++] = kv.second; } }
int pf_rcount(void) { return (int)pf_rset.size(); }
// dump (key, firstframe) pairs: out must hold 2*count uint64
void pf_wdump(uint64_t *out) { size_t i = 0; for (auto &kv : pf_wset) { out[i++] = kv.first; out[i++] = (uint64_t)kv.second; } }
void pf_rdump(uint64_t *out) { size_t i = 0; for (auto &kv : pf_rset) { out[i++] = kv.first; out[i++] = (uint64_t)kv.second; } }
void pf_stats(uint64_t *out)
{
	out[0] = (uint64_t)pf_minS; out[1] = pf_nmi_count; out[2] = pf_nmi_maxdur; out[3] = pf_nmi_mingap; out[4] = pf_nmi_nested;
}
void pf_reset(void)
{
	memset(pf_cov, 0, sizeof(pf_cov)); memset(pf_ramexec, 0, sizeof(pf_ramexec)); memset(pf_vals, 0, sizeof(pf_vals));
	if (pf_regs) memset(pf_regs, 0, (size_t)PRGsize[0] * 96);
	memset(pf_intpc, 0, sizeof(pf_intpc));
	pf_wset.clear(); pf_rset.clear(); pf_pend.clear(); pf_vecpos.clear(); pf_intret.clear();
	pf_minS = 0x1FF; pf_nmi_t0 = 0; pf_in_nmi = 0; pf_nmi_maxdur = 0; pf_nmi_mingap = ~0ULL; pf_nmi_count = 0; pf_nmi_nested = 0;
	pf_cur_off = -2; pf_cur_op = 0xEA;
}
}
#endif
