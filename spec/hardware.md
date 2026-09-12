# pcM Hardware & Software Environment

Audited 2026-09-12. All values recorded from the actual machine, not assumed.

## Hardware

| Item | Value |
|---|---|
| Machine | Apple Mac14,2 (MacBook Air M2) |
| CPU | Apple M2 |
| Architecture | arm64 |
| Logical cores | 8 |
| Physical cores | 8 |
| RAM | 8 GiB (8589934592 bytes) |
| OS | macOS 26.6.2 (build 25G83) |

**Commands used**

```bash
sw_vers
sysctl -n machdep.cpu.brand_string hw.ncpu hw.physicalcpu hw.memsize hw.model
uname -m
```

## Software

| Component | Version / Path |
|---|---|
| Cardinal | `snapshot-20-10-27-54609-g8b05495ce0` at `/Users/kavyawadhwa/MOOSE/cardinal/cardinal-opt` |
| OpenMC (embedded in Cardinal, **this is the solver**) | `v0.15.3-190-g66359e5dd` (`install/lib/libopenmc.dylib`) |
| OpenMC Python API (input generation only) | `0.15.1.dev0` in conda env `openmc` |
| NekRS | `/Users/kavyawadhwa/MOOSE/cardinal/install/bin/nekrs` |
| MOOSE framework | conda env `moose` (moose-libmesh 2026.06.05, moose-petsc 3.25.2, mpich) |
| MPI | mpich (`mpiexec` in env `moose`) |
| Conda root | `/Users/kavyawadhwa/Anaconda/anaconda3` |

## Nuclear data

| Item | Value |
|---|---|
| Library | ENDF/B-VIII.0 (HDF5) |
| Path | `/Users/kavyawadhwa/Documents/Digital Twin/nuclear_data/endfb-viii.0-hdf5/cross_sections.xml` |
| `OPENMC_CROSS_SECTIONS` | set in `~/.zshrc` (not exported in non-interactive shells — scripts must set it explicitly) |

Checksum of the library to be recorded before the production run.

## NekRS backend determination

the project protocol requires that GPU acceleration must be demonstrated, never assumed.
Inspected `build/nekrs/CMakeCache.txt`:

```
ENABLE_CUDA:BOOL=0
ENABLE_HIP:BOOL=0
ENABLE_OPENCL:BOOL=0
ENABLE_METAL:BOOL=OFF
ENABLE_DPCPP:BOOL=ON
ENABLE_HYPRE_GPU:BOOL=OFF
NEKRS_GPU_MPI:BOOL=OFF
```

**Conclusion: NekRS is CPU-only on this machine.** No CUDA, HIP, OpenCL, or
Metal backend is compiled. `ENABLE_DPCPP=ON` is nominal only — DPCPP targets
Intel oneAPI devices, which do not exist on an Apple M2. The Apple GPU is
therefore unusable for NekRS, as the project protocol anticipated.

**Consequence:** all NekRS work runs on 8 Apple M2 CPU cores with 8 GiB of
shared RAM. This is the binding constraint on model scope (see
`spec/operating.md`, model-scope decision).

## Deviation from approved specification: OpenMC version

The approved specification names **OpenMC 0.16.0**. Three different versions
are in play on this machine and none is 0.16.0:

| Role | Version |
|---|---|
| Requested by spec | 0.16.0 |
| Cardinal's embedded solver (computes k) | v0.15.3-190-g66359e5dd |
| Python API used to write XML inputs | 0.15.1.dev0 |

This is recorded, not silently accepted (project protocol integrity rule 8). Impact
assessment and the question for the supervisor are in `PCM_STATUS.md`.

## Environment reproduction

```bash
export PATH="/Users/kavyawadhwa/Anaconda/anaconda3/envs/moose/bin:$PATH"
export OPENMC_CROSS_SECTIONS="/Users/kavyawadhwa/Documents/Digital Twin/nuclear_data/endfb-viii.0-hdf5/cross_sections.xml"
export CARDINAL="/Users/kavyawadhwa/MOOSE/cardinal/cardinal-opt"
```

Note: `conda activate` fails under this session's non-interactive shell
(`__conda_exe: permission denied`). Absolute paths to env binaries are used
instead, which is more reproducible anyway.
