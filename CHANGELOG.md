# Changelog

## v0.1.0-alpha.1 — First official Alpha baseline (release preparation, 19 October 2026)

Baseline source commit: `9bfc2f7`. The version is designated for the first official Alpha release; creation of the Git tag and publication of the GitHub release have not yet been confirmed.

### Added and consolidated

- Tkinter desktop GUI with authentication, account setup, message composition, Received and Sent views.
- Bidirectional Tor Onion SMTP messaging with end-to-end encryption, Ed25519 authenticity verification and X25519 trust/pinning.
- SQLCipher encryption at rest for Received, Sent and Queue databases, using a password-unlocked DEK.
- Authenticated GSAT v1 encrypted attachment storage, including metadata.
- Offline application password recovery and DEK rewrapping/key-rotation flows.
- GUI background send handling and improved pipeline diagnostics.

### Validation

- 1844 developer tests passed in the last confirmed full suite.
- Developer and Ubuntu VM: self-send and bidirectional delivery validated, including attachments.
- Both systems: Received, Sent and Queue lacked plaintext SQLite headers; attachment GSAT v1 format checked read-only.

### Known limitations

- No independent professional security audit; Alpha use only.
- CLI `start` bootstrap without a DEK fails closed; functional limitation, not evidence of plaintext access.
- The updated installer/dependencies and clean-install packaging for this exact release were not freshly revalidated in the latest milestone.
- No existing-data migration or upgrade-path certification is claimed.

## v0.0.1-alpha — Historical development baseline

- Initial project structure and Python package definition.
- Early development milestone (historical tag, distinct from `v0.1.0-alpha.1`).
