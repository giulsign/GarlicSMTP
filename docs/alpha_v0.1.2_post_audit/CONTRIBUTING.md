# Contributing to GarlicSMTP

Thank you for your interest in contributing to GarlicSMTP through code review, testing, documentation, bug reports, or independent security assessment.

GarlicSMTP is a **source-available** project maintained by Giuliano Signorelli. Original GarlicSMTP code is made available under the **PolyForm Noncommercial License 1.0.0**; separate commercial licenses may be granted by the copyright holder. Source availability does **not** mean that the project uses an OSI-approved open-source license. Read [LICENSE](LICENSE), [NOTICE](NOTICE), [COMMERCIAL-LICENSE.md](COMMERCIAL-LICENSE.md), and [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

## Contributor License Agreement (CLA)

Contributions intended for inclusion in the official project must comply with [CLA.md](CLA.md). Each pull request containing a contribution must explicitly include this statement, exactly as written in the CLA:

> I have read and agree to the GarlicSMTP Contributor License Agreement (CLA.md), and I have the right to submit this contribution under those terms.

Contributions without the required confirmation must not be merged. Read the actual agreement before accepting it; this guide is not a replacement for the CLA.

Contributors retain copyright in their original contributions. Under the CLA, they grant the maintainer specified copyright and patent rights, including rights relevant to separate commercial licensing. Submit only material you have the right to contribute. Clearly identify third-party material and its provenance, copyright, and license. Do not submit generated or derived material whose licensing or provenance cannot be established.

## Development baseline and release status

The project maintainer has confirmed that:

- the GitHub repository contains the **`v0.1.2-alpha`** Git tag;
- `pyproject.toml` and `garlicsmtp/__init__.py` both declare the Python package version **`0.1.2a0`**;
- the code has been consolidated in the repository.

These are maintainer confirmations, not an independent inspection of the tagged commit. **A Git tag does not by itself establish that a GitHub Release, validated wheel, or source distribution has been published.** Do not claim artifact qualification without checking the actual artifact and its provenance.

Base proposed changes on the checked-out implementation and the corresponding tests, rather than on historical audit findings or archived documentation alone. Use a separate branch or fork; do not rewrite the tagged baseline.

## Before changing code: inspect, test, then modify

1. Inspect the relevant implementation, configuration, installer manifests, and nearby tests before proposing a change.
2. Describe the expected behavior and, where practical, reproduce a confirmed defect with a focused failing test (**RED**).
3. Make the smallest suitable change (**GREEN**), then run relevant regression tests.
4. Run the complete test suite before proposing a merge. The latest maintainer-reported development baseline passed **1,993 tests**; this historical result does not guarantee the outcome of subsequent runs or independently qualify tagged distribution artifacts.
5. For changes involving operating systems, packaging, Tor, cryptography, databases, or GUI behavior, test in the relevant environment and state exactly what was and was not verified.

For an activated Python virtual environment:

```bash
python -m pytest -q
```

The documented installer manifest declares profiles for **Ubuntu 24.04**, **Kali 2026.1**, and **Debian 13**. A declared profile is not a guarantee of universal compatibility. WSL Ubuntu is a development environment, not a validated native Windows distribution target.

Do not overwrite unrelated work or include unrelated cleanup. Stage only the intended changes. Every pull request should explain the behavior changed, motivation, tests and results, affected platforms, and known limitations.

## Dependencies and third-party licensing

Before adding, replacing, bundling, or upgrading a dependency, identify its upstream source, version or version range, applicable license, required notices, and role as a runtime, system, build, development, or test dependency. Consider transitive dependencies and native components contained in wheels or other distribution artifacts.

The documented Python runtime dependencies are:

- `dnspython>=2.8,<3`
- `cryptography>=46,<47`
- `sqlcipher3==0.6.3`

The Linux installation manifest also declares Tor and Tkinter/Tcl/Tk-related system prerequisites. **Tkinter is the current GUI toolkit; PySide6 is not an application dependency.** Do not treat a developer's entire `pip freeze` output as the distribution dependency list.

Preserve required notices, assess potentially restrictive or incompatible license obligations before acceptance, and update [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) where appropriate. The project's license does not relicense third-party components. Check notices and bundled native dependencies against the actual artifacts before claiming distribution compliance.

## Security, privacy, and test data

GarlicSMTP is **experimental Alpha software** and has not undergone an independent professional security audit or certification. Never commit or attach real mailbox databases, messages, Onion Service private keys, Tor cookies, credentials, data-encryption keys (DEKs), recovery material, or unredacted logs containing secrets. Use synthetic fixtures and protect existing user data and Onion identities.

Report suspected vulnerabilities privately using [SECURITY.md](SECURITY.md), rather than opening a public issue with exploit details or sensitive data.

The integrated audit records successful experimental Onion-to-Onion SMTP exchanges in both directions during **T0–T4** and **T8**. T8 used temporary outbound `nftables` filtering on two test hosts, with Tor-mediated connectivity observed. These results establish only the behavior tested; they do not prove universal network isolation, absence of all leaks, guaranteed anonymity, or security certification. See the [integrated audit and T8 report](docs/GarlicSMTP_Integrated_Audit_2026-11-05_T8.md) and [SECURITY.md](SECURITY.md).

The documented input and attachment limits are:

| Constraint | Limit |
| --- | --- |
| SMTP input line | 64 KiB |
| Total SMTP message | 2 MiB (2,097,152 bytes) |
| Application attachment | 1 MiB (1,048,576 bytes) |

Changes to SMTP, MIME processing, attachments, transport, storage, queue handling, or security controls should include focused boundary tests and relevant regressions. These implementation limits are not a guarantee of successful delivery or immunity to resource exhaustion.

## Pull requests and review

Submit changes through the repository's normal pull-request workflow, including:

- the **exact CLA acceptance statement** above;
- a concise description of the change and why it is needed;
- reproducible test commands, results, and environment details;
- compatibility, security, migration, and third-party licensing implications, where relevant;
- remaining limitations or unverified assumptions.

Documentation changes should reflect the implementation and should distinguish current behavior from historical reports. Dated audit findings are evidence about the revisions they examined: do not automatically label them as currently open or resolved without issue-specific verification.

Independent review and reproducible test reports are welcome. Acceptance is at the maintainer's discretion; no merge or response deadline is guaranteed.

## Contact

For licensing questions, contact **giulisign@gmail.com**. For security reports, follow [SECURITY.md](SECURITY.md).
