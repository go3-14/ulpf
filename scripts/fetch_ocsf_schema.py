"""Dev-time helper placeholder for fetching official OCSF schemas.

Runtime code never imports this file. The current repository ships a documented
trimmed schema subset so the project remains runnable in air-gapped demos.
"""


def main():
    raise SystemExit(
        "Official OCSF fetch is intentionally not wired in this offline build. "
        "Replace this script with a schema-server crawler before claiming full OCSF validation."
    )


if __name__ == "__main__":
    main()
