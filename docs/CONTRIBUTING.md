# Contributing to GarlicSMTP

Thank you for your interest in contributing to GarlicSMTP.

GarlicSMTP is a **source-available** project maintained by Giuliano Signorelli. Original GarlicSMTP code is made available under the **PolyForm Noncommercial License 1.0.0**; the copyright holder may grant separate commercial licenses. Source availability does not mean that the project is licensed under an OSI-approved open-source license. See `LICENSE`, `NOTICE`, `COMMERCIAL-LICENSE.md`, and `THIRD_PARTY_LICENSES.md`.

## Contributor License Agreement (CLA)

Code contributions can be accepted only from contributors who agree to the GarlicSMTP Contributor License Agreement in `CLA.md`. Every pull request containing a contribution must explicitly include the following confirmation:

> I have read and agree to the GarlicSMTP Contributor License Agreement (CLA.md), and I have the right to submit this contribution under those terms.

Contributions without that confirmation must not be merged. Read the actual `CLA.md` before agreeing; this guide does not replace its terms.

## Copyright and contribution rights

Contributors retain copyright in their original contributions. As described in `CLA.md`, the agreement grants the maintainer rights to use, modify, distribute, sublicense, and relicense accepted contributions, including in separately licensed commercial versions. The authoritative terms are those of the CLA itself.

Submit only material that you created and have the right to license, that you are legally authorized to contribute, or that is clearly identified as third-party material with its provenance, copyright, and applicable license. Do not copy code from another project without identifying its source and license. Do not submit generated or derived code when its provenance or licensing permissions cannot be established.

## Development baseline and release status

The working project version for the upcoming release is **`0.1.1a0`**, with **`v0.1.1-alpha`** as the planned release label. This is a release candidate under preparation, **not a claim that the Git tag or GitHub release has been published**. The earlier `v0.1.0-alpha.1` baseline and commit `9bfc2f7` are historical references, not the current development baseline. The latest reported development commit before the version/documentation updates was `8faf1c6`.

Develop changes on a separate branch or fork, and base them on the actual checked-out source rather than assumptions drawn from older documentation. Never rewrite a historical release or claim that an uncreated tag exists.

## Before changing code: inspect, test, then modify

1. Read the existing implementation, relevant configuration, installation manifests, and nearby tests **before** proposing a correction or refactor.
2. Identify the expected behavior and reproduce the problem with a focused failing test where practical (**RED**).
3. Implement the smallest change that satisfies the test (**GREEN**), then run relevant regression tests.
4. Run the full test suite before proposing a merge; the latest reported run for the `0.1.1a0` preparation passed **1,974 tests**, but that historical result does not validate future changes.
5. For changes crossing OS, packaging, Tor, cryptography, database, or GUI boundaries, validate in the relevant target environment and describe what was actually tested. The installer manifest currently declares **Ubuntu 24.04**; a separate Ubuntu 22.04 VM was used for some GUI validation. Do not represent either as universal platform support.

For the existing Python virtual environment, the test command is:

```bash
python -m pytest -q
```

Do not introduce unrelated cleanup or overwrite unrelated working-tree changes. Stage only the intended files, not `git add .` by default. Include a concise description of behavior, tests, platform, and any remaining limitations in the pull request.

## Dependencies and licensing

Before adding, replacing, bundling, or upgrading third-party software, identify its upstream source, exact version or version range, license and required notices, and whether it is a runtime, system, build, development, or test dependency. Check transitive dependencies and native components bundled in binary wheels or release artifacts.

The currently declared Python runtime dependencies are `dnspython>=2.8,<3`, `cryptography>=46,<47`, and `sqlcipher3==0.6.3`. The Linux installation manifest also declares Tor and Python Tkinter/Tcl/Tk prerequisites. **PySide6 is not used by the current application**, even if it remains installed in an individual developer's environment. Do not infer distributed dependencies from `pip freeze` alone.

Copyleft, source-disclosure, noncommercial, commercial, or otherwise restrictive license obligations require review before acceptance. Preserve required third-party notices and update `THIRD_PARTY_LICENSES.md` when appropriate. Do not assume the GarlicSMTP license relicenses third-party code.

## Security, privacy, and test data

Treat GarlicSMTP as security-sensitive Alpha software. Never commit or attach live mailbox databases, messages, Onion Service private keys, Tor authentication cookies, passwords, data-encryption keys (DEKs), recovery material, credentials, or logs containing secrets. Use synthetic fixtures and redact sensitive diagnostic data. Avoid destructive changes to user data or Onion identities.

Potential vulnerabilities should be reported privately under `SECURITY.md`, not initially disclosed in public issues. Do not claim that tests or successful Tor communication constitute an independent security audit or guarantee anonymity.

## Pull requests and review

Contributions should normally be developed in a separate branch or fork and submitted through a pull request. Include the required CLA statement, a summary of the change, its motivation, tests performed and results, and any compatibility, security, migration, or licensing implications. Documentation should be kept consistent with the behavior actually implemented.

Acceptance is at the maintainer's discretion; submitting a contribution does not guarantee that it will be merged. No specific review or merge time is guaranteed.

## Licensing questions

For commercial licensing questions, contact **giulisign@gmail.com** or use the official GarlicSMTP repository where appropriate.
