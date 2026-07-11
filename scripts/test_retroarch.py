from services.retroarch import (
    RetroArchDiscovery,
    CoreScanner,
    RetroArchReport,
)



discovery = RetroArchDiscovery()


retroarch = discovery.find_retroarch()


cores = []


directory = (
    discovery.find_core_directory()
)


if directory:

    scanner = CoreScanner(
        directory
    )

    cores = scanner.scan()



report = RetroArchReport(
    discovery,
    cores
)


print(
    report.generate()
)
