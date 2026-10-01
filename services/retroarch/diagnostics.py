class LaunchDiagnostics:
    def explain(self, report):
        if report.get("reasons"):
            return list(report["reasons"])
        messages = []
        if not report["retroarch"]:
            messages.append("RetroArch was not found.")
        if not report["core"]:
            messages.append("Required core is missing.")
        if not report["rom"]:
            messages.append("ROM file does not exist.")
        return messages or ["File prerequisites passed; production presentation and launch checks still apply."]
