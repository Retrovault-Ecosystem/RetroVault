# RetroVault

Current roadmap: **USQE — Usability, Scale and Qualified Expansion**.
**Milestone #1 decision/documentation baseline complete; #2–#12 unstarted.** See [USQE roadmap](docs/usability_scale_qualified_expansion_roadmap.md) and [decision baseline](docs/usqe_milestone1_decisions.md).
The original roadmap stays closed and protected; this is not Milestone #15.

Original roadmap status: **Milestone #14 and the approved 14-milestone roadmap COMPLETE**.
See [current milestone](docs/current_milestone.md), the [M14 integration record](docs/milestone14_final_integration.md)
and [setup instructions](docs/configuration_startup.md) for verified support and limits.
The overview below includes project direction; it is not a claim that every future feature
or external integration is currently qualified. No new roadmap is started by M14.

## The Ultimate Retro Gaming Management Ecosystem

RetroVault is a Linux-first desktop application designed to manage, organize, customize, and enhance retro gaming collections.

Built around RetroArch, ES-DE, and the Linux gaming ecosystem, RetroVault provides a unified interface for:

- ROM library management
- RetroArch core detection
- Game metadata
- Artwork management
- Overlays and bezels
- Shader management
- Theme customization
- Launch profiles
- Collection organization

---

# Features

## Library Management

- Automatic ROM scanning
- Platform detection
- Core association
- Game filtering
- Favorites
- Artwork support

## RetroArch Integration

- Core management
- Launch configuration
- System profiles
- Shader support
- Overlay support

## Customization

Future support:

- ES-DE themes
- RetroArch overlays
- CRT shaders
- Bezels
- Wallpapers
- Controller profiles

---

# Project Status

RetroVault is currently under active development.

Current milestone:

**Milestone #13 — Standalone emulators — COMPLETE AND CLOSED.**

See [standalone emulator contracts](docs/milestone13_standalone_emulators.md) for the opt-in native Linux Snes9x backend, settings and qualification.
Milestone #12 remains closed; see [advanced visual contracts](docs/milestone12_advanced_visuals.md) for existing RetroArch CRT controls.
See [configuration and startup](docs/configuration_startup.md) for reproducible setup,
explicit RVDB bundle installation, first-run behavior, configuration precedence and
setting activation. [Current milestone](docs/current_milestone.md) records acceptance
and [architecture contracts](docs/architecture_contracts.md) preserves ownership.

The RVDB consumer bundle remains Git-ignored runtime data installed explicitly from
a validated producer artifact. Application startup does not download, rebuild or
silently locate a sibling RVDB checkout.

---

# Technology

Built with:

- Python
- PyQt6
- RetroArch
- Linux

---

# Development

Clone:

```bash
git clone git@github.com:Retrovault-Ecosystem/Retrovault.git

```

## Architecture contracts

The current ownership, identity, persistence, presentation, and execution contracts
are documented in [Architecture contracts](docs/architecture_contracts.md).
Historical milestone records remain available in `docs/current_milestone.md`.


## Run from a checkout

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m scripts.install_rvdb_bundle /absolute/path/to/rvdb.bundle.json
.venv/bin/python -B -m scripts.check_startup
.venv/bin/python app.py
```

Install `requirements-dev.txt` for tests and artwork tooling. Fresh defaults do not
scan personal ROM directories. Configure sources, cores and RetroArch in Settings.
An absolute path to `app.py` can be launched from another working directory.
