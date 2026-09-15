# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.


from pathlib import Path

from install.validator import (
    load_install_manifest,
    validate_repository,
)


def generate_installer(
    *,
    project_root: Path,
    output_path: Path | None = None,
    validate=validate_repository,
    load_manifest=load_install_manifest,
) -> Path:
    errors = validate(project_root)

    if errors:
        raise ValueError("\n".join(errors))

    if output_path is None:
        output_path = project_root / "install.sh"

    manifest = load_manifest(
        project_root / "install" / "manifest.toml"
    )
    python_executable = (
        manifest["platform"]["profiles"][0]
        ["python"]["executable"]
    )

    output_path.write_text(
        (
            "#!/bin/sh\n"
            'cd "$(dirname "$0")"\n'
            f"{python_executable} -m install.installer\n"
        ),
        encoding="utf-8",
    )
    output_path.chmod(0o755)

    return output_path


def main(
    *,
    generate=generate_installer,
) -> None:
    project_root = (
        Path(__file__).resolve().parents[1]
    )

    generate(
        project_root=project_root,
    )


if __name__ == "__main__":
    main()