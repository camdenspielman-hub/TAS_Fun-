// pf_search ANALYSIS additions (appended to the harness driver; same FCEUX core objects).
// Nothing here changes emulation: the hooks only OBSERVE (registered X6502_MemHook callbacks).
//
// 1. Bit-level taint tracker ("non-interference checker").
//    Question it answers, for ONE emulated frame from a loaded state s with pad input a:
//      "If some bits K of some RAM bytes of s, and some pad bits KIN of a, were different,
//       would the frame end in a state that differs from the actual one ONLY in RAM bits
//       that are listed as allowed?"
//    It follows the executed instruction stream (exec hook, called before each instruction
//    with the pre-instruction registers) and propagates a per-bit taint mask through
//    registers, flags and RAM.  It ABORTS (= answer "not proven") whenever a tainted value
//    could change control flow, an address, the stack pointer, an I/O register, the I flag,
//    or anything it does not model.  Under no abort, control flow, addresses, cycle counts and
//    all I/O are identical for every value of the tainted bits, so only data taint remains.
//    The final check (registers/flags/DB untainted, RAM taint inside the allowed bits) is done
//    by the caller from pf_taint_status().
// 2. Read watch: logs (frame, pc, addr, value) of CPU reads of watched addresses (any mode,
//    incl. dummy and DMA reads).
#include "cart.h"
#ifndef RM2_NO_MEMHOOK
extern uint8 *RAM;

enum { M_ILL, M_ADC, M_AND, M_ASL, M_BCC, M_BCS, M_BEQ, M_BIT, M_BMI, M_BNE, M_BPL, M_BRK, M_BVC, M_BVS, M_CLC, M_CLD,
       M_CLI, M_CLV, M_CMP, M_CPX, M_CPY, M_DEC, M_DEX, M_DEY, M_EOR, M_INC, M_INX, M_INY, M_JMP, M_JSR, M_LDA, M_LDX,
       M_LDY, M_LSR, M_NOP, M_ORA, M_PHA, M_PHP, M_PLA, M_PLP, M_ROL, M_ROR, M_RTI, M_RTS, M_SBC, M_SEC, M_SED, M_SEI,
       M_STA, M_STX, M_STY, M_TAX, M_TAY, M_TSX, M_TXA, M_TXS, M_TYA };
enum { A_IMP, A_ACC, A_IMM, A_ZP, A_ZPX, A_ZPY, A_ABS, A_ABX, A_ABY, A_IND, A_IZX, A_IZY, A_REL };
struct PfOp { uint8 m, a; };
static PfOp pf_op[256];
static int pf_op_init = 0;
static void pf_init_optab(void)
{
	static const int T[][3] = {
		{0x00,M_BRK,A_IMP},{0x01,M_ORA,A_IZX},{0x05,M_ORA,A_ZP},{0x06,M_ASL,A_ZP},{0x08,M_PHP,A_IMP},{0x09,M_ORA,A_IMM},
		{0x0A,M_ASL,A_ACC},{0x0D,M_ORA,A_ABS},{0x0E,M_ASL,A_ABS},{0x10,M_BPL,A_REL},{0x11,M_ORA,A_IZY},{0x15,M_ORA,A_ZPX},
		{0x16,M_ASL,A_ZPX},{0x18,M_CLC,A_IMP},{0x19,M_ORA,A_ABY},{0x1D,M_ORA,A_ABX},{0x1E,M_ASL,A_ABX},{0x20,M_JSR,A_ABS},
		{0x21,M_AND,A_IZX},{0x24,M_BIT,A_ZP},{0x25,M_AND,A_ZP},{0x26,M_ROL,A_ZP},{0x28,M_PLP,A_IMP},{0x29,M_AND,A_IMM},
		{0x2A,M_ROL,A_ACC},{0x2C,M_BIT,A_ABS},{0x2D,M_AND,A_ABS},{0x2E,M_ROL,A_ABS},{0x30,M_BMI,A_REL},{0x31,M_AND,A_IZY},
		{0x35,M_AND,A_ZPX},{0x36,M_ROL,A_ZPX},{0x38,M_SEC,A_IMP},{0x39,M_AND,A_ABY},{0x3D,M_AND,A_ABX},{0x3E,M_ROL,A_ABX},
		{0x40,M_RTI,A_IMP},{0x41,M_EOR,A_IZX},{0x45,M_EOR,A_ZP},{0x46,M_LSR,A_ZP},{0x48,M_PHA,A_IMP},{0x49,M_EOR,A_IMM},
		{0x4A,M_LSR,A_ACC},{0x4C,M_JMP,A_ABS},{0x4D,M_EOR,A_ABS},{0x4E,M_LSR,A_ABS},{0x50,M_BVC,A_REL},{0x51,M_EOR,A_IZY},
		{0x55,M_EOR,A_ZPX},{0x56,M_LSR,A_ZPX},{0x58,M_CLI,A_IMP},{0x59,M_EOR,A_ABY},{0x5D,M_EOR,A_ABX},{0x5E,M_LSR,A_ABX},
		{0x60,M_RTS,A_IMP},{0x61,M_ADC,A_IZX},{0x65,M_ADC,A_ZP},{0x66,M_ROR,A_ZP},{0x68,M_PLA,A_IMP},{0x69,M_ADC,A_IMM},
		{0x6A,M_ROR,A_ACC},{0x6C,M_JMP,A_IND},{0x6D,M_ADC,A_ABS},{0x6E,M_ROR,A_ABS},{0x70,M_BVS,A_REL},{0x71,M_ADC,A_IZY},
		{0x75,M_ADC,A_ZPX},{0x76,M_ROR,A_ZPX},{0x78,M_SEI,A_IMP},{0x79,M_ADC,A_ABY},{0x7D,M_ADC,A_ABX},{0x7E,M_ROR,A_ABX},
		{0x81,M_STA,A_IZX},{0x84,M_STY,A_ZP},{0x85,M_STA,A_ZP},{0x86,M_STX,A_ZP},{0x88,M_DEY,A_IMP},{0x8A,M_TXA,A_IMP},
		{0x8C,M_STY,A_ABS},{0x8D,M_STA,A_ABS},{0x8E,M_STX,A_ABS},{0x90,M_BCC,A_REL},{0x91,M_STA,A_IZY},{0x94,M_STY,A_ZPX},
		{0x95,M_STA,A_ZPX},{0x96,M_STX,A_ZPY},{0x98,M_TYA,A_IMP},{0x99,M_STA,A_ABY},{0x9A,M_TXS,A_IMP},{0x9D,M_STA,A_ABX},
		{0xA0,M_LDY,A_IMM},{0xA1,M_LDA,A_IZX},{0xA2,M_LDX,A_IMM},{0xA4,M_LDY,A_ZP},{0xA5,M_LDA,A_ZP},{0xA6,M_LDX,A_ZP},
		{0xA8,M_TAY,A_IMP},{0xA9,M_LDA,A_IMM},{0xAA,M_TAX,A_IMP},{0xAC,M_LDY,A_ABS},{0xAD,M_LDA,A_ABS},{0xAE,M_LDX,A_ABS},
		{0xB0,M_BCS,A_REL},{0xB1,M_LDA,A_IZY},{0xB4,M_LDY,A_ZPX},{0xB5,M_LDA,A_ZPX},{0xB6,M_LDX,A_ZPY},{0xB8,M_CLV,A_IMP},
		{0xB9,M_LDA,A_ABY},{0xBA,M_TSX,A_IMP},{0xBC,M_LDY,A_ABX},{0xBD,M_LDA,A_ABX},{0xBE,M_LDX,A_ABY},{0xC0,M_CPY,A_IMM},
		{0xC1,M_CMP,A_IZX},{0xC4,M_CPY,A_ZP},{0xC5,M_CMP,A_ZP},{0xC6,M_DEC,A_ZP},{0xC8,M_INY,A_IMP},{0xC9,M_CMP,A_IMM},
		{0xCA,M_DEX,A_IMP},{0xCC,M_CPY,A_ABS},{0xCD,M_CMP,A_ABS},{0xCE,M_DEC,A_ABS},{0xD0,M_BNE,A_REL},{0xD1,M_CMP,A_IZY},
		{0xD5,M_CMP,A_ZPX},{0xD6,M_DEC,A_ZPX},{0xD8,M_CLD,A_IMP},{0xD9,M_CMP,A_ABY},{0xDD,M_CMP,A_ABX},{0xDE,M_DEC,A_ABX},
		{0xE0,M_CPX,A_IMM},{0xE1,M_SBC,A_IZX},{0xE4,M_CPX,A_ZP},{0xE5,M_SBC,A_ZP},{0xE6,M_INC,A_ZP},{0xE8,M_INX,A_IMP},
		{0xE9,M_SBC,A_IMM},{0xEA,M_NOP,A_IMP},{0xEC,M_CPX,A_ABS},{0xED,M_SBC,A_ABS},{0xEE,M_INC,A_ABS},{0xF0,M_BEQ,A_REL},
		{0xF1,M_SBC,A_IZY},{0xF5,M_SBC,A_ZPX},{0xF6,M_INC,A_ZPX},{0xF8,M_SED,A_IMP},{0xF9,M_SBC,A_ABY},{0xFD,M_SBC,A_ABX},
		{0xFE,M_INC,A_ABX}};
	for (int i = 0; i < 256; i++) { pf_op[i].m = M_ILL; pf_op[i].a = A_IMP; }
	for (unsigned i = 0; i < sizeof(T) / sizeof(T[0]); i++) { pf_op[T[i][0]].m = T[i][1]; pf_op[T[i][0]].a = T[i][2]; }
	pf_op_init = 1;
}

// abort reasons
enum { PFA_NONE = 0, PFA_ILLEGAL = 1, PFA_IDX = 2, PFA_PTR = 3, PFA_BRANCH = 4, PFA_IOWRITE = 5, PFA_DMA = 6,
       PFA_PLP = 7, PFA_RET = 8, PFA_BRK = 9, PFA_TXS = 10, PFA_S = 11, PFA_JREAD = 12, PFA_IOMODE = 13, PFA_CODE = 14 };

static uint8 t_ram[0x800];
static uint8 tA, tX, tY, tN, tV, tZ, tC;
static int t_on = 0, t_abort = 0, t_abort_pc = -1, t_abort_op = -1;
static uint8 t_kin = 0;                 // pad bits whose value is "symbolic" (tainted source)
static int t_jrb = 0, t_lstrobe = 0;    // mirror of input.cpp joy_readbit[0] and LastStrobe
static int t_jexp = 0, t_jseen = 0;     // predicted / observed $4016 reads of the current instruction
static int t_have_prev = 0, t_expS = 0, t_touch = 0, t_last_touch = 0, t_last_flags_pre = 0;
static long t_ninstr = 0, t_ntainted = 0, t_nint = 0;

static inline void t_fail(int why, int pc, int op)
{
	if (!t_abort) { t_abort = why; t_abort_pc = pc; t_abort_op = op; }
}
static inline uint8 pk(uint32 a)        // side-effect-free peek (RAM, WRAM, PRG); I/O -> 0 (never used for I/O)
{
	a &= 0xFFFF;
	if (a < 0x2000) return RAM[a & 0x7FF];
	if (a >= 0x6000) return Page[a >> 11][a];
	return 0;
}
static inline int isram(uint32 a) { return (a & 0xFFFF) < 0x2000; }
static inline uint8 lowmask_from(uint8 t) // bits >= lowest set bit of t (carry chain)
{
	if (!t) return 0;
	int k = 0; while (!((t >> k) & 1)) k++;
	return (uint8)(0xFF << k);
}
static inline void setNZ(uint8 tr, uint8 vr, int known)
{
	tN = (tr >> 7) & 1;
	if (!tr) tZ = 0;
	else if (known && (vr & (uint8)~tr)) tZ = 0;   // an untainted 1 bit fixes Z = 0
	else tZ = 1;
}
// Data read of the byte at a (by the current instruction). Returns its taint; *v/*known = concrete value if known.
static inline uint8 rd(uint32 a, uint8 *v, int *known, int pc, int mode)
{
	a &= 0xFFFF;
	if (a < 0x2000) { *v = RAM[a & 0x7FF]; *known = 1; uint8 t = t_ram[a & 0x7FF]; if (t) t_touch = 1; return t; }
	if (a >= 0x6000) { *v = Page[a >> 11][a]; *known = 1; return 0; }
	*v = 0; *known = 0;
	if (a >= 0x4000 && a < 0x6000) {
		// open-bus bits (X.DB) can only enter here; require DB to come from the instruction stream
		if (!(mode == A_ABS || mode == A_ABX || mode == A_ABY)) t_fail(PFA_IOMODE, pc, a);
		if (a == 0x4016) {
			int idx = t_jrb + t_jexp;
			t_jexp++;
			if (idx < 8 && ((t_kin >> idx) & 1)) return 1;   // bit 0 of the read = pad bit idx
		}
	}
	return 0;
}
static inline void wr(uint32 a, uint8 t, uint8 v, int pc)
{
	a &= 0xFFFF;
	if (a < 0x2000) { t_ram[a & 0x7FF] = t; if (t) t_touch = 1; return; }
	if (t) { t_fail(PFA_IOWRITE, pc, a); return; }
	if (a == 0x4014) {   // OAM DMA copies page v into OAM
		uint32 base = ((uint32)v) << 8;
		if (base < 0x2000) { for (int i = 0; i < 256; i++) if (t_ram[(base + i) & 0x7FF]) { t_fail(PFA_DMA, pc, a); return; } }
		else if (base >= 0x4000 && base < 0x6000) t_fail(PFA_DMA, pc, a);
	}
}
static inline uint8 flagbyte(void) { return (uint8)((tN << 7) | (tV << 6) | (tZ << 1) | tC); }

static void t_exec_hook(unsigned int pc, unsigned int, void *)
{
	if (!t_on || t_abort) return;
	if (t_have_prev) {
		if (t_jseen != t_jexp) { t_fail(PFA_JREAD, pc, t_jseen * 16 + t_jexp); return; }
		if (X.S != (t_expS & 0xFF)) {
			if (((t_expS - 3) & 0xFF) == X.S) {      // interrupt entry (NMI): PCH, PCL, P pushed
				t_ram[0x100 + (t_expS & 0xFF)] = 0;
				t_ram[0x100 + ((t_expS - 1) & 0xFF)] = 0;
				t_ram[0x100 + ((t_expS - 2) & 0xFF)] = flagbyte();
				t_nint++;
			} else { t_fail(PFA_S, pc, X.S); return; }
		}
	}
	t_jseen = 0; t_jexp = 0; t_touch = 0;
	t_last_flags_pre = flagbyte();
	t_ninstr++;
	if (pc < 0x6000) { t_fail(PFA_CODE, pc, -1); return; }    // code outside PRG/WRAM: not modelled
	uint8 op = pk(pc);
	PfOp oi = pf_op[op];
	if (oi.m == M_ILL) { t_fail(PFA_ILLEGAL, pc, op); return; }
	uint8 o1 = pk(pc + 1), o2 = pk(pc + 2);
	uint8 vA = X.A, vX = X.X, vY = X.Y, vS = X.S, vP = X.P;
	uint32 ea = 0;
	int S2 = vS;
	switch (oi.a) {
	case A_ZP: ea = o1; break;
	case A_ZPX: if (tX) { t_fail(PFA_IDX, pc, op); return; } ea = (o1 + vX) & 0xFF; break;
	case A_ZPY: if (tY) { t_fail(PFA_IDX, pc, op); return; } ea = (o1 + vY) & 0xFF; break;
	case A_ABS: ea = o1 | (o2 << 8); break;
	case A_ABX: if (tX) { t_fail(PFA_IDX, pc, op); return; } ea = ((o1 | (o2 << 8)) + vX) & 0xFFFF; break;
	case A_ABY: if (tY) { t_fail(PFA_IDX, pc, op); return; } ea = ((o1 | (o2 << 8)) + vY) & 0xFFFF; break;
	case A_IZX: {
		if (tX) { t_fail(PFA_IDX, pc, op); return; }
		uint8 p = (o1 + vX) & 0xFF;
		if (t_ram[p] | t_ram[(p + 1) & 0xFF]) { t_fail(PFA_PTR, pc, op); return; }
		ea = RAM[p] | (RAM[(p + 1) & 0xFF] << 8); break; }
	case A_IZY: {
		uint8 p = o1;
		if (t_ram[p] | t_ram[(p + 1) & 0xFF]) { t_fail(PFA_PTR, pc, op); return; }
		if (tY) { t_fail(PFA_IDX, pc, op); return; }
		ea = ((RAM[p] | (RAM[(p + 1) & 0xFF] << 8)) + vY) & 0xFFFF; break; }
	case A_IND: {
		uint32 p = o1 | (o2 << 8), p2 = ((p + 1) & 0xFF) | (p & 0xFF00);
		if ((isram(p) && t_ram[p & 0x7FF]) || (isram(p2) && t_ram[p2 & 0x7FF])) { t_fail(PFA_PTR, pc, op); return; }
		break; }
	default: break;
	}
	uint8 tM = 0, vM = 0; int known = 1;
	int m = oi.m;
	// operand fetch for reading instructions
	switch (m) {
	case M_ADC: case M_AND: case M_BIT: case M_CMP: case M_CPX: case M_CPY: case M_EOR: case M_LDA: case M_LDX: case M_LDY:
	case M_ORA: case M_SBC:
		if (oi.a == A_IMM) { tM = 0; vM = o1; known = 1; }
		else tM = rd(ea, &vM, &known, pc, oi.a);
		break;
	case M_ASL: case M_LSR: case M_ROL: case M_ROR: case M_INC: case M_DEC:
		if (oi.a == A_ACC) { tM = tA; vM = vA; known = 1; }
		else {
			tM = rd(ea, &vM, &known, pc, oi.a);
			// RMW on a non-RAM address also writes the OLD value back first (dummy write): it must be untainted
			if (!isram(ea) && tM) { t_fail(PFA_IOWRITE, pc, ea); return; }
		}
		break;
	default: break;
	}
	if (t_abort) return;
	switch (m) {
	case M_LDA: tA = tM; setNZ(tM, vM, known); break;
	case M_LDX: tX = tM; setNZ(tM, vM, known); break;
	case M_LDY: tY = tM; setNZ(tM, vM, known); break;
	case M_STA: wr(ea, tA, vA, pc); break;
	case M_STX: wr(ea, tX, vX, pc); break;
	case M_STY: wr(ea, tY, vY, pc); break;
	case M_AND: {
		uint8 tr;
		if (known) tr = (uint8)((tA & (vM | tM)) | (tM & (vA | tA)));
		else tr = (uint8)(tA | (tM & (vA | tA)));
		tA = tr; setNZ(tr, (uint8)(vA & vM), known); break; }
	case M_ORA: {
		uint8 tr;
		if (known) tr = (uint8)((tA & ((uint8)~vM | tM)) | (tM & ((uint8)~vA | tA)));
		else tr = (uint8)(tA | (tM & ((uint8)~vA | tA)));
		tA = tr; setNZ(tr, (uint8)(vA | vM), known); break; }
	case M_EOR: { uint8 tr = tA | tM; tA = tr; setNZ(tr, (uint8)(vA ^ vM), known); break; }
	case M_ADC: case M_SBC: {
		uint8 tin = tA | tM;
		if (!tin && !tC) { tA = 0; tN = tV = tZ = tC = 0; break; }
		uint8 tr = tC ? 0xFF : lowmask_from(tin);
		uint32 l = (m == M_ADC) ? (uint32)(vA + vM + (vP & 1)) : (uint32)(vA - vM - ((vP & 1) ^ 1));
		tA = tr; tC = 1; tV = 1; setNZ(tr, (uint8)l, known); break; }
	case M_CMP: case M_CPX: case M_CPY: {
		uint8 treg = (m == M_CMP) ? tA : (m == M_CPX ? tX : tY);
		uint8 vreg = (m == M_CMP) ? vA : (m == M_CPX ? vX : vY);
		uint8 tt = treg | tM;
		if (!tt) { tN = tZ = tC = 0; break; }
		tN = 1; tC = 1; tZ = (known && ((vreg ^ vM) & (uint8)~tt)) ? 0 : 1; break; }
	case M_BIT: {
		tN = (tM >> 7) & 1; tV = (tM >> 6) & 1;
		uint8 tr = known ? (uint8)((tA & (vM | tM)) | (tM & (vA | tA))) : (uint8)(tA | (tM & (vA | tA)));
		tZ = (!tr) ? 0 : ((known && ((vA & vM) & (uint8)~tr)) ? 0 : 1); break; }
	case M_ASL: case M_LSR: case M_ROL: case M_ROR: case M_INC: case M_DEC: {
		uint8 tr, vr; uint8 tco = tC;
		switch (m) {
		case M_ASL: tr = (uint8)(tM << 1); vr = (uint8)(vM << 1); tC = (tM >> 7) & 1; break;
		case M_LSR: tr = (uint8)(tM >> 1); vr = (uint8)(vM >> 1); tC = tM & 1; break;
		case M_ROL: tr = (uint8)((tM << 1) | tco); vr = (uint8)((vM << 1) | (vP & 1)); tC = (tM >> 7) & 1; break;
		case M_ROR: tr = (uint8)((tM >> 1) | (tco << 7)); vr = (uint8)((vM >> 1) | ((vP & 1) << 7)); tC = tM & 1; break;
		case M_INC: tr = lowmask_from(tM); vr = (uint8)(vM + 1); break;
		default: tr = lowmask_from(tM); vr = (uint8)(vM - 1); break;
		}
		setNZ(tr, vr, known);
		if (oi.a == A_ACC) tA = tr;
		else wr(ea, tr, vr, pc);
		break; }
	case M_INX: { uint8 tr = lowmask_from(tX); tX = tr; setNZ(tr, (uint8)(vX + 1), 1); break; }
	case M_DEX: { uint8 tr = lowmask_from(tX); tX = tr; setNZ(tr, (uint8)(vX - 1), 1); break; }
	case M_INY: { uint8 tr = lowmask_from(tY); tY = tr; setNZ(tr, (uint8)(vY + 1), 1); break; }
	case M_DEY: { uint8 tr = lowmask_from(tY); tY = tr; setNZ(tr, (uint8)(vY - 1), 1); break; }
	case M_TAX: tX = tA; setNZ(tA, vA, 1); break;
	case M_TAY: tY = tA; setNZ(tA, vA, 1); break;
	case M_TXA: tA = tX; setNZ(tX, vX, 1); break;
	case M_TYA: tA = tY; setNZ(tY, vY, 1); break;
	case M_TSX: tX = 0; tN = 0; tZ = 0; break;
	case M_TXS: if (tX) { t_fail(PFA_TXS, pc, op); return; } S2 = vX; break;
	case M_BPL: case M_BMI: if (tN) { t_fail(PFA_BRANCH, pc, op); return; } break;
	case M_BVC: case M_BVS: if (tV) { t_fail(PFA_BRANCH, pc, op); return; } break;
	case M_BCC: case M_BCS: if (tC) { t_fail(PFA_BRANCH, pc, op); return; } break;
	case M_BNE: case M_BEQ: if (tZ) { t_fail(PFA_BRANCH, pc, op); return; } break;
	case M_CLC: case M_SEC: tC = 0; break;
	case M_CLV: tV = 0; break;
	case M_CLI: case M_SEI: case M_CLD: case M_SED: case M_NOP: case M_JMP: break;
	case M_PHA: t_ram[0x100 + vS] = tA; if (tA) t_touch = 1; S2 = vS - 1; break;
	case M_PHP: t_ram[0x100 + vS] = flagbyte(); if (flagbyte()) t_touch = 1; S2 = vS - 1; break;
	case M_PLA: { uint8 a = (vS + 1) & 0xFF; tA = t_ram[0x100 + a]; if (tA) t_touch = 1; setNZ(tA, RAM[0x100 + a], 1); S2 = vS + 1; break; }
	case M_PLP: { uint8 a = (vS + 1) & 0xFF; uint8 tb = t_ram[0x100 + a];
		if (tb & 0x3C) { t_fail(PFA_PLP, pc, op); return; }
		if (tb) t_touch = 1;
		tN = (tb >> 7) & 1; tV = (tb >> 6) & 1; tZ = (tb >> 1) & 1; tC = tb & 1; S2 = vS + 1; break; }
	case M_JSR: t_ram[0x100 + vS] = 0; t_ram[0x100 + ((vS - 1) & 0xFF)] = 0; S2 = vS - 2; break;
	case M_RTS: if (t_ram[0x100 + ((vS + 1) & 0xFF)] | t_ram[0x100 + ((vS + 2) & 0xFF)]) { t_fail(PFA_RET, pc, op); return; }
		S2 = vS + 2; break;
	case M_RTI: { uint8 tb = t_ram[0x100 + ((vS + 1) & 0xFF)];
		if (tb & 0x3C) { t_fail(PFA_PLP, pc, op); return; }
		if (t_ram[0x100 + ((vS + 2) & 0xFF)] | t_ram[0x100 + ((vS + 3) & 0xFF)]) { t_fail(PFA_RET, pc, op); return; }
		if (tb) t_touch = 1;
		tN = (tb >> 7) & 1; tV = (tb >> 6) & 1; tZ = (tb >> 1) & 1; tC = tb & 1; S2 = vS + 3; break; }
	case M_BRK: t_fail(PFA_BRK, pc, op); return;
	default: t_fail(PFA_ILLEGAL, pc, op); return;
	}
	if (t_touch) t_ntainted++;
	t_last_touch = t_touch;
	t_expS = S2 & 0xFF;
	t_have_prev = 1;
}

// ---- read watch ----
static uint8 rw_mask[0x10000 / 8];
static int rw_on = 0;
struct RWHit { int frame; int pc; int addr; int val; };
static std::vector<RWHit> rw_hits;
static int rw_lastpc = -1;

static void t_read_hook(unsigned int addr, unsigned int val, void *)
{
	if (t_on && addr == 0x4016) { t_jseen++; t_jrb = (t_jrb + 1) & 0xFF; }
	if (rw_on && (rw_mask[(addr & 0xFFFF) >> 3] >> (addr & 7) & 1)) {
		RWHit h; h.frame = g_frameno; h.pc = X.PC; h.addr = addr & 0xFFFF; h.val = val & 0xFF;
		if (rw_hits.size() < 4000000) rw_hits.push_back(h);
	}
}
// ---- write watch (same mask format as the read watch) ----
static uint8 ww_mask[0x10000 / 8];
static int ww_on = 0;
static std::vector<RWHit> ww_hits;
static void t_write_hook(unsigned int addr, unsigned int val, void *)
{
	if (ww_on && (ww_mask[(addr & 0xFFFF) >> 3] >> (addr & 7) & 1)) {
		RWHit h; h.frame = g_frameno; h.pc = X.PC; h.addr = addr & 0xFFFF; h.val = val & 0xFF;
		if (ww_hits.size() < 4000000) ww_hits.push_back(h);
	}
	if (t_on && addr == 0x4016) {
		if ((t_lstrobe & 1) && !(val & 1)) t_jrb = 0;
		t_lstrobe = val & 1;
	}
}
static int pf_hooks_installed = 0;
static void pf_install(void)
{
	if (pf_hooks_installed) return;
	if (!pf_op_init) pf_init_optab();
	X6502_MemHook::Add(X6502_MemHook::Exec, t_exec_hook, nullptr);
	X6502_MemHook::Add(X6502_MemHook::Read, t_read_hook, nullptr);
	X6502_MemHook::Add(X6502_MemHook::Write, t_write_hook, nullptr);
	pf_hooks_installed = 1;
}

extern "C" {
// Begin tracking for the next emulated frame(s). init: 0x800 bytes of initial RAM taint masks.
void pf_taint_begin(const uint8 *init, int kin, int jrb, int lstrobe)
{
	pf_install();
	memcpy(t_ram, init, 0x800);
	tA = tX = tY = tN = tV = tZ = tC = 0;
	t_abort = 0; t_abort_pc = -1; t_abort_op = -1;
	t_kin = (uint8)kin; t_jrb = jrb & 0xFF; t_lstrobe = lstrobe & 1;
	t_jexp = t_jseen = 0; t_have_prev = 0; t_expS = 0; t_touch = 0; t_last_touch = 0; t_last_flags_pre = 0;
	t_ninstr = t_ntainted = t_nint = 0;
	t_on = 1;
}
// End tracking; out[0..15]: abort, abort_pc, abort_op, tA, tX, tY, flags(now), flags(at last instr start),
// last_touch, ninstr, ntainted, nint, final-S-ok(1)/interrupt-pending(2)/bad(0). ram_out: 0x800 taint bytes.
void pf_taint_end(int *out, uint8 *ram_out)
{
	if (t_on && !t_abort && t_have_prev) {
		if (t_jseen != t_jexp) t_fail(PFA_JREAD, -2, t_jseen * 16 + t_jexp);
	}
	int sok = 1;
	if (t_on && !t_abort && t_have_prev && X.S != (t_expS & 0xFF)) {
		if (((t_expS - 3) & 0xFF) == X.S) {   // interrupt taken after the last instruction
			t_ram[0x100 + (t_expS & 0xFF)] = 0;
			t_ram[0x100 + ((t_expS - 1) & 0xFF)] = 0;
			t_ram[0x100 + ((t_expS - 2) & 0xFF)] = flagbyte();
			sok = 2;
		} else { t_fail(PFA_S, -3, X.S); sok = 0; }
	}
	t_on = 0;
	out[0] = t_abort; out[1] = t_abort_pc; out[2] = t_abort_op; out[3] = tA; out[4] = tX; out[5] = tY;
	out[6] = flagbyte(); out[7] = t_last_flags_pre; out[8] = t_last_touch; out[9] = (int)t_ninstr;
	out[10] = (int)t_ntainted; out[11] = (int)t_nint; out[12] = sok; out[13] = t_have_prev;
	if (ram_out) memcpy(ram_out, t_ram, 0x800);
}
void pf_rw_set(int addr, int on) { addr &= 0xFFFF; if (on) rw_mask[addr >> 3] |= (1 << (addr & 7)); else rw_mask[addr >> 3] &= ~(1 << (addr & 7)); }
void pf_rw_clearmask(void) { memset(rw_mask, 0, sizeof(rw_mask)); }
void pf_rw(int on) { pf_install(); rw_on = on; }
void pf_rw_reset(void) { rw_hits.clear(); }
int pf_rw_count(void) { return (int)rw_hits.size(); }
void pf_rw_get(int i, int *out) { const RWHit &h = rw_hits[i]; out[0] = h.frame; out[1] = h.pc; out[2] = h.addr; out[3] = h.val; }
int pf_hooks(void) { return pf_hooks_installed; }
void pf_ww_set(int addr, int on) { addr &= 0xFFFF; if (on) ww_mask[addr >> 3] |= (1 << (addr & 7)); else ww_mask[addr >> 3] &= ~(1 << (addr & 7)); }
void pf_ww_clearmask(void) { memset(ww_mask, 0, sizeof(ww_mask)); }
void pf_ww(int on) { pf_install(); ww_on = on; }
void pf_ww_reset(void) { ww_hits.clear(); }
int pf_ww_count(void) { return (int)ww_hits.size(); }
void pf_ww_get(int i, int *out) { const RWHit &h = ww_hits[i]; out[0] = h.frame; out[1] = h.pc; out[2] = h.addr; out[3] = h.val; }
}
#endif
