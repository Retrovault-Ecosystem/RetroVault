# RetroVault Durable-State Baseline

## Purpose

This document records the known-good durable-state boundary immediately
before development of the Bulk Import feature.

The baseline is intentionally small. It preserves the validated NES and
SNES games used during RetroVault launch, presentation, and runtime
development so that Bulk Import can be tested against an existing Library
rather than an empty one.

## Protected parent

`97b73fdb74605c6f83300420b33423bde39393e3`

Branch:

`feature/rvdb-foundation`

## Seed Library

The known-good Library contains exactly two games:

- NES — DuckTales 2
- SNES — Street Fighter II Turbo

Both ROM paths existed at closure time.

The seed Library is intentional. Bulk Import must preserve these existing
entries and must not create duplicates when scanning content already known
to RetroVault.

## Durable user state

The closure baseline includes:

- `config.json`
- `library.json`
- `library-state.json`
- `collections.json`
- `presentation-state.json`
- `runtime.json`

These files remain user state under `~/.config/retrovault` and are not
copied into the repository.

Known-good SHA-256 fingerprints at closure:

- `config.json`
  `04c06b2bf340447b5fb8dc7fa73c7c7acbe747e95cdf3ce3fcd30236eb358d4b`
- `library.json`
  `ae516283830f665391d66332b0a60c51b5610f5c42b12fda0728f633c72cb890`
- `library-state.json`
  `90454d3dcf658f1835f5c43cc7c3c6f069f2a7850b052c52f1bc7daa7005d6b7`
- `collections.json`
  `c8081119dcb2df23dc068601113bf2999dcdf2a05073ba6fa1da4057636a9e27`
- `presentation-state.json`
  `a1adb2fd8cd5cc48110b13c5beb04c55389a1e9bab25179aa9c4ae2b3ce731e2`
- `runtime.json`
  `f1765eb5d23dc9cb6e78aea5b501f407695ad10f3c62c02e774a83d7bad7a2df`

## Preserved behavior

At closure:

- existing Library entries resolve to physical ROM files;
- favorites/recent state remains durable;
- collections remain durable;
- presentation assignments remain durable;
- RetroArch runtime configuration remains durable;
- recursive ROM scanning already exists at the scanner layer;
- the focused Library/state regression suite passes.

## Cache classification

`~/.cache/retrovault` is transient runtime/development storage.

The existing cache contains historical validation, calibration, proof,
staging, and backup material accumulated during NES/SNES development.
It is not part of the durable Library contract.

Cache cleanup is deliberately separated from durable-state cleanup so that
historical proof material is not destroyed as part of this checkpoint.

## Bulk Import boundary

Bulk Import begins after this baseline.

The implementation must build on the existing RetroVault scanner and
Library architecture rather than introducing a parallel ROM discovery
system.

Initial invariants:

1. Preserve existing Library entries.
2. Do not duplicate an already-known ROM.
3. Scan configured sources recursively.
4. Resolve supported ROMs through the existing RVDB boundary.
5. Ignore unsupported/non-ROM files.
6. Produce deterministic Library results.
7. Preserve favorites, recent history, collections, and presentation state.
8. Treat import as a Library operation, not a presentation/runtime mutation.
