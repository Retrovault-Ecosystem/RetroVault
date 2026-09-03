from services.retroarch.validator import (
    LaunchValidator,
)


def make_validator():
    return LaunchValidator(
        "/unused/retroarch",
        "/unused/core",
    )


def test_missing_rom_is_not_valid(
    tmp_path,
):
    validator = make_validator()

    rom = (
        tmp_path
        / "missing.nes"
    )

    assert (
        validator.check_rom(
            str(rom)
        )
        is False
    )


def test_directory_is_not_valid_rom(
    tmp_path,
):
    validator = make_validator()

    rom = (
        tmp_path
        / "rom-directory"
    )

    rom.mkdir()

    assert (
        validator.check_rom(
            str(rom)
        )
        is False
    )


def test_zero_byte_placeholder_is_not_valid_rom(
    tmp_path,
):
    validator = make_validator()

    rom = (
        tmp_path
        / "placeholder.nes"
    )

    rom.touch()

    assert rom.stat().st_size == 0

    assert (
        validator.check_rom(
            str(rom)
        )
        is False
    )


def test_nonempty_regular_file_is_valid_rom_candidate(
    tmp_path,
):
    validator = make_validator()

    rom = (
        tmp_path
        / "game.nes"
    )

    rom.write_bytes(
        b"NES\x1a"
    )

    assert rom.stat().st_size > 0

    assert (
        validator.check_rom(
            str(rom)
        )
        is True
    )
