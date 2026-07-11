from services.retroarch import (
    LaunchValidator,
    LaunchDiagnostics
)



validator = LaunchValidator(

    "/usr/bin/retroarch",

    "/opt/retropie/libretrocores/lr-genesis-plus-gx/genesis_plus_gx_libretro.so"

)



result = validator.validate(

    "/games/sonic.md"

)



print(result)



diagnostics = LaunchDiagnostics()


print(

    diagnostics.explain(
        result
    )

)
