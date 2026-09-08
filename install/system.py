# Copyright (c) Giuliano Signorelli
#
# See LICENSE for the full license terms.


def build_package_install_action(
    profile: dict,
    plan: dict,
) -> dict | None:
    if not plan["packages"]:
        return None

    package_manager = profile["package_manager"]

    if package_manager != "apt-get":
        raise ValueError(
            f"unsupported package manager: {package_manager}"
        )

    system_prerequisites = profile.get("system_prerequisites")

    if system_prerequisites is None:
        raise ValueError(
            "profile system_prerequisites is required"
        )

    declared_packages = {
        prerequisite["package"]
        for prerequisite in system_prerequisites.values()
    }

    for package in plan["packages"]:
        if package not in declared_packages:
            raise ValueError(
                f"package not declared by profile: {package}"
            )

    return {
        "command": [
            package_manager,
            "install",
            "-y",
            *plan["packages"],
        ],
        "requires_privileges": True,
    }