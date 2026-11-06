# GarlicSMTP — QUICKLAUNCH

> **Project version:** `0.1.2a0`. **Git tag:** `v0.1.2-alpha` (maintainer-confirmed on GitHub).
> **Source baseline:** tagged `v0.1.2-alpha` source; this documentation review has not independently checked the tag commit or inspected packaged release artifacts.
> **Development regression:** 1,993 tests passed (`python -m pytest -q`) during the completed audit; this is not an independent security audit or a clean-install qualification.
> **Scope:** this is not proof of a fresh installation on Ubuntu 24.04, Kali 2026.1, or Debian 13, nor a release packaging validation. Earlier developer ↔ Ubuntu VM attachment checks and the 5 November 2026 T0–T4/T8 Onion SMTP experiments are distinct from installer qualification.
> **Security:** no independent professional audit, comprehensive backup/temporary-file review, or verified legacy plaintext migration.

**Quick guide for installing and starting GarlicSMTP without prior Python knowledge.**
Updated: 06/11/2026 · Documentation target: GarlicSMTP `0.1.2a0`, Git tag `v0.1.2-alpha`. This guide reconciles historical installation instructions, maintainer-confirmed version/tag status and the 5 November integrated audit; it does not certify a fresh installation.

## Before you begin

The installation manifest declares profiles for **Ubuntu 24.04, Kali 2026.1, and Debian 13**. The steps below focus on Ubuntu 24.04 Desktop. A fresh clean installation from the exact tagged `v0.1.2-alpha` source has not been certified on all three profiles. You need an Internet connection, a regular user account able to authorize installation of system prerequisites, and the official public repository `https://github.com/giulsign/GarlicSMTP.git`.

**Windows:** WSL Ubuntu is a development environment, **not** a native Windows release target. **macOS and other Linux distributions:** no validated installation is claimed here. Kali and Debian use their own declared manifest profiles; this Ubuntu walkthrough is not a guarantee of identical behavior on those systems.

## A. Installing on Ubuntu 24.04 — copy one block at a time

### 1. Open Terminal

On Ubuntu press `Ctrl` + `Alt` + `T`.

### 2. Check Git

```bash
git --version
```

If you see “command not found”, install Git:

```bash
sudo apt-get update
sudo apt-get install git
```

### 3. Clone the repository

Copy the **entire** block. Use the official project repository URL:

```bash
cd ~
git clone https://github.com/giulsign/GarlicSMTP.git GarlicSMTP
cd ~/GarlicSMTP
```

The repository is public and cloning it normally requires no credentials. **Before installing, select the confirmed version tag** rather than assuming that the default branch points to the same code:

```bash
git fetch --tags
git switch --detach v0.1.2-alpha
```

The detached HEAD state is expected when selecting a tag. If either command fails, stop and retain the error message; do not substitute an arbitrary branch or commit. This procedure selects the tagged source, but does **not** constitute a validated clean-install test or establish that downloadable release packages exist.

### 4. Run the installer

```bash
./install.sh
```

**Important:** do NOT run `sudo ./install.sh`. The installer handles any authorization requests needed for system packages. Do not use `sudo pip` or a global `pip install`. At the `IMAP password:` prompt, enter the IMAP service password, which is separate from the GUI password. Wait for completion and read any errors.

### 5. If required, log out of Ubuntu and log back in

The installer may arrange access to the Tor cookie through the `debian-tor` system group. If the GUI cannot start Tor after installation, **log out of the graphical session completely and log back in**; opening a new terminal alone may not suffice.

### 6. Start GarlicSMTP

Use the **GarlicSMTP** Desktop icon, if present, or run:

```bash
~/.local/share/garlicsmtp/venv/bin/garlicsmtp-gui
```

This path automatically uses the current user's home directory; you do not need to substitute your username.

### 7. First login and basic use

Follow the account setup screen, choose personal credentials and keep the password secure. There is no default password. GUI credentials are separate from the Onion address. The **offline recovery key is implemented**: during initial setup, record it and store it off the device, following the GUI confirmation step. Do not share it or store it alongside your password.

After login, start the services in the interface and check Tor and runtime status. To send, use the compose section and enter the recipient; read incoming messages in **Received** and messages accepted for sending in **Sent**. A message in Sent has not necessarily been delivered to the remote recipient.

### 8. Optional custom Onion HTML presence page

In the GUI preferences, find the Onion presence page settings. To enable a custom page, provide the path to an **existing HTML file**; a blank path or a directory is not valid when the option is enabled. Save the preferences and **restart the relevant service/application** for the change to take effect. The default page remains available when customization is disabled. Do not put passwords, private keys, recovery material or other secrets in a publicly served HTML file. The HTML template in `docs/personalized_html/` is a project example, not a required installation step.

## B. If a message does not send

1. Check that services and Tor are operational. If necessary, refresh Tor services from the GarlicSMTP panel.
2. Check for queued items. **Retry pending** makes pending messages eligible for an immediate retry; it **does not send directly** or certify delivery. QueueWorker retries on its next tick.
3. If Tor is congested, wait and retry; if the issue persists, try another Internet connection. `Tor ready` means local Tor is available, not that the remote `.onion` peer is reachable.
4. Do not delete databases or Onion identities to “repair” a temporary failure.

GarlicSMTP enforces an SMTP input line limit of **64 KiB** and a total SMTP message limit of **2 MiB (2,097,152 bytes)**. The separate application attachment limit remains **1 MiB (1,048,576 bytes)**. These limits are not a guarantee that every remote peer accepts the same message size.

### Transport verification context (5 November 2026)

The integrated audit records T0–T4 Onion-to-Onion SMTP checks between a WSL2 Ubuntu host and an Ubuntu 24.04 VirtualBox VM, with conventional DNS TCP/UDP port 53 blocked in the test scenarios. T8 additionally applied **temporary** bilateral `nftables` OUTPUT restrictions permitting loopback and traffic from the Tor service user; direct outbound attempts were blocked, SOCKS5/Tor connections succeeded, and Onion SMTP delivery succeeded in both directions. The temporary firewall rules were removed and cleanup checked. These observations apply **only to the tested environments**; they are not an anonymity guarantee, a default installer feature, or a procedure to copy onto an end-user machine. The T8 tests do not establish new attachment, upgrade or installer validation.

## C. Development startup in WSL Ubuntu (not the user installation)

For developers, from a repository **already present with `.venv` already created**:

```bash
cd /mnt/c/garlicsmtp
source .venv/bin/activate
python -m garlicsmtp.gui
```

Development CLI, when needed:

```bash
python -m garlicsmtp.cli
```

Do not substitute `garlicsmtp-gui` for `python -m garlicsmtp.gui` during development: these entry points use different path choices.

## D. Updates, repairs and uninstallation

- Do not delete `~/.local/share/garlicsmtp/` or regenerate identities or keys to attempt an update.
- Idempotent reinstallation through `./install.sh` was validated historically; **it is not a password reset command**.
- The source checkout `~/GarlicSMTP` must be preserved during uninstallation. Uninstallation may remove application-owned persistent state, including the Onion identity: examine the options and documentation of the actual repository command first. The documented command is `python3 -m install.uninstaller` from the repository root: its confirmation prompt requires `DELETE`, and the operation is destructive to application state, including keys and Onion identities. Inspect the current implementation and make backups before deliberately using it. It does not remove the source checkout.
- Before updating code through Git, verify the branch, remote and working-tree state; do not blindly run `git pull` over local changes.

## E. Quick checks (read-only)

```bash
lsb_release -a
python3 --version
git --version
ls -l ~/.local/share/garlicsmtp/venv/bin/garlicsmtp-gui
```

If any step fails, **stop there** and retain the complete error message. Do not run random commands found online or share passwords, private keys or Tor cookie contents.

**Privacy note:** E2EE in transit and encryption at rest are separate layers. In this baseline the three databases use SQLCipher with a DEK, and attachments use GSAT v1 with ChaCha20-Poly1305. Exported files remain readable; comprehensive protection of backups, temporary files and private keys has not been established.

## Version, unlocking and verification (`v0.1.2-alpha`)

- **GUI setup:** choose a strong password; when the offline recovery key is displayed, store it and acknowledge it. It allows recovery and setting a new password without replacing the DEK.
- **Login:** password-based unlocking is required before GUI construction and receiving services start. If unlocking fails, the application must remain closed (fail-closed).
- **Forgotten password:** use the GUI recovery procedure with the recovery key. Do not reinstall or delete persistent state to recover the account.
- **Attachments:** encrypted at rest inside the application store; an attachment saved/exported outside that store is a new readable file for anyone with access to its destination.
- **Verification:** the previous baseline included developer/VM self-send, developer → VM, VM → developer and attachment tests, plus limited SQLCipher header and GSAT v1 observations. The reported internal development suite had **1,993 passed**; the 5 November T0–T4/T8 audit separately documents bidirectional Onion SMTP transport under the tested configurations. Neither establishes that the exact Git tag or installation artifacts passed a fresh installation and regression cycle.
- **Limitations:** alternative CLI/bootstrap/receiving paths were under review at the documented checkpoint; backups and temporary remnants were not comprehensively assessed; no legacy migration or independent cryptographic audit.

## Sources and release

Repository: https://github.com/giulsign/GarlicSMTP.git. The maintainer confirms that `pyproject.toml` and `garlicsmtp/__init__.py` declare **`0.1.2a0`**, and that Git tag **`v0.1.2-alpha`** is present on GitHub. These facts were not independently checked against the tagged commit during this documentation update. Declared runtime dependencies: `dnspython>=2.8,<3`, `cryptography>=46,<47`, `sqlcipher3==0.6.3`; the Linux installer profiles also require Tor, Python virtual environments, and Python Tkinter. PySide6 is not a current runtime dependency. The existence, publication and validation of `0.1.2a0` GitHub Release assets, wheels or source distributions have **not** been established. A plain `git clone` follows the current default branch, not necessarily the tagged baseline; use the explicit tag selection shown above. Do not update or reinstall over real data without an agreed procedure.

**Destructive uninstallation, only when explicitly intended:** from the checkout root, `python3 -m install.uninstaller`, with `DELETE` confirmation; is intended to remove application data and the Onion identity while preserving the source checkout; verify the current implementation before use. Do not use this as a password reset.
