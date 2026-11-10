"""pf_static dynamic recorder (ANALYSIS ONLY; REAL replays, no pokes).
Replays a movie from power-on with librm2rec.so (= FCEUX master core objects + native recorders, built by
tools/proof/Makefile) in a fresh process and saves, under OUTDIR/TAG:
  <tag>_cov.npy      uint16[PRG]  bit b set = instruction start executed while PRG bank b was mapped at $8000
  <tag>_ramexec.npy  uint8[65536] executed PCs outside PRG ROM (must be all zero)
  <tag>_vals.npy     uint8[2048,32] value bitsets of every value written to each RAM byte
  <tag>_intpc.npy    uint32[65536] histogram of the last instruction before each NMI/IRQ entry
  <tag>_intret.npy   uint32[n,2] (return PC << 8 | mapped bank, count): exact interrupted boundaries
  <tag>_w.npy / _r.npy  uint64[n,2] (key, first frame), key = id<<16 | addr; id = PRG offset of the instruction,
                          0x80000+PC for non-ROM PCs, 0xFFFFF = interrupt-entry push
  <tag>_regs.npz     offs (executed PRG offsets), regs [n,96] = A/X/Y value bitsets at the instruction boundary
  <tag>_stats.json   min stack pointer, NMI count / max duration / min spacing (CPU cycles) / nesting count
usage: pfrec.py MOVIE.fm2|PADS.json TAG ROM.nes librm2rec.so OUTDIR [extra_frames] [reads(0/1)]
(needs numpy)"""
import os, sys, json, time, hashlib, ctypes
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'harness'))
import rm2  # noqa: E402


def main():
    if len(sys.argv) < 6:
        raise SystemExit(__doc__)
    mvp, tag, rom, lib, outdir = sys.argv[1:6]
    extra = int(sys.argv[6]) if len(sys.argv) > 6 else 0
    reads = int(sys.argv[7]) if len(sys.argv) > 7 else 1
    if mvp.endswith('.fm2'):
        hdr, frames = rm2.read_fm2(mvp)
        assert all(c == 0 for c, p in frames), 'movie with reset/power commands'
        mv = [p for c, p in frames]
    else:
        mv = json.load(open(mvp))
    os.makedirs(outdir, exist_ok=True)
    e = rm2.Emu(lib, rom)
    L = e.lib
    L.pf_regs_enable(); L.pf_reset(); L.pf_start(reads)
    t0 = time.time()
    n = len(mv)
    lag = 0
    for f in range(n + extra):
        lag += e.frame(mv[f] if f < n else 0)
        if f == n - 1:
            b = e.ramblock()
            print('after last movie frame %d: ram md5 %s stage %02X alienHP %d' % (f, hashlib.md5(b).hexdigest(), b[0x2A], b[0x6C1]), flush=True)
        if f % 20000 == 0:
            print(f, '%.0fs' % (time.time() - t0), flush=True)
    L.pf_stop()
    W = os.path.join(outdir, tag)
    psz = L.pf_prgsize()
    cov = np.zeros(psz, np.uint16); L.pf_cov_get(cov.ctypes.data_as(ctypes.c_void_p), psz); np.save(W + '_cov.npy', cov)
    rg = np.zeros((psz, 96), np.uint8); L.pf_regs_get(rg.ctypes.data_as(ctypes.c_void_p))
    nz = np.nonzero(rg.any(axis=1))[0]
    np.savez_compressed(W + '_regs.npz', offs=nz.astype(np.int32), regs=rg[nz])
    rx = np.zeros(65536, np.uint8); L.pf_ramexec_get(rx.ctypes.data_as(ctypes.c_void_p)); np.save(W + '_ramexec.npy', rx)
    vals = np.zeros((2048, 32), np.uint8); L.pf_vals_get(vals.ctypes.data_as(ctypes.c_void_p)); np.save(W + '_vals.npy', vals)
    ip = np.zeros(65536, np.uint32); L.pf_intpc_get(ip.ctypes.data_as(ctypes.c_void_p)); np.save(W + '_intpc.npy', ip)
    for kind, cnt, dump in (('w', L.pf_wcount, L.pf_wdump), ('r', L.pf_rcount, L.pf_rdump)):
        c = cnt(); a = np.zeros((c, 2), np.uint64); dump(a.ctypes.data_as(ctypes.c_void_p)); np.save(W + '_%s.npy' % kind, a)
        print(kind, 'distinct (instr,addr) pairs:', c)
    c = L.pf_intret_count(); a = np.zeros((c, 2), np.uint32); L.pf_intret_dump(a.ctypes.data_as(ctypes.c_void_p))
    np.save(W + '_intret.npy', a)
    print('distinct interrupt return points (pc,bank):', c)
    st = np.zeros(5, np.uint64); L.pf_stats(st.ctypes.data_as(ctypes.c_void_p))
    stats = dict(frames=n + extra, movie_frames=n, lag_frames=lag, minS=int(st[0]), nmi_count=int(st[1]),
                 nmi_max_cycles=int(st[2]), nmi_min_gap_cycles=int(st[3]), nmi_nested=int(st[4]),
                 movie=mvp, md5_movie=hashlib.md5(open(mvp, 'rb').read()).hexdigest())
    json.dump(stats, open(W + '_stats.json', 'w'), indent=1)
    print(stats)
    print('executed instr starts', int((cov != 0).sum()), 'ram-exec PCs', int((rx != 0).sum()), 'time %.0fs' % (time.time() - t0))

if __name__ == '__main__':
    main()
