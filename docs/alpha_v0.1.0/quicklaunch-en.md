# GarlicSMTP — QUICKLAUNCH

> **Reference version: v0.1.0-alpha.1 — 19/10/2026.**
> Application baseline: commit `9bfc2f7` on `main`, already pushed to `origin/main` according to the development checkpoint.
> **The Git tag/release has not yet been confirmed as created:** a generic clone of `main` does not guarantee an immutable build.
> Bidirectional developer ↔ Ubuntu VM sending/receiving and attachments validated; developer suite: **1844 passed**.
> Received, Sent and Queue databases were found without plaintext SQLite headers on both machines; a GSAT v1 attachment was observed on both.
> These results do not constitute an independent audit, secure backup validation or migration of legacy archives.

**Quick guide for installing and starting GarlicSMTP without prior Python knowledge.**
Updated: 19/10/2026 · Documentation release: `v0.1.0-alpha.1`. Tests and operational checks are user-reported checkpoints; no fresh clean installation was performed while preparing this document.

## Before you begin

This procedure has **documented validation for Ubuntu 24.04 Desktop**. You need an Internet connection, a regular user account able to authorize installation of system prerequisites, and the official public repository `https://github.com/giulsign/GarlicSMTP.git`.

**Windows:** documented as a development host through WSL Ubuntu, **not** as a native Windows installation target. **macOS and other Linux distributions:** no officially validated installation is recorded in the snapshots.

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

Copy the **entire** block. If prompted, paste the actual Git URL supplied by the project and press Enter:

```bash
cd ~
git clone https://github.com/giulsign/GarlicSMTP.git GarlicSMTP
cd ~/GarlicSMTP
```

The repository is public and cloning it normally requires no credentials.

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

## B. If a message does not send

1. Check that services and Tor are operational. If necessary, refresh Tor services from the GarlicSMTP panel.
2. Check for queued items. **Retry pending** makes pending messages eligible for an immediate retry; it **does not send directly** or certify delivery. QueueWorker retries on its next tick.
3. If Tor is congested, wait and retry; if the issue persists, try another Internet connection. `Tor ready` means local Tor is available, not that the remote `.onion` peer is reachable.
4. Do not delete databases or Onion identities to “repair” a temporary failure.

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
- The source checkout `~/GarlicSMTP` must be preserved during uninstallation. Uninstallation may remove application-owned persistent state, including the Onion identity: examine the options and documentation of the actual repository command first. The documented command is `python3 -m install.uninstaller` from the repository root: it requires `DELETE` and irreversibly deletes all application data, including keys and Onion identities. It does not remove the source checkout.
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

## Version, unlocking and verification (v0.1.0-alpha.1)

- **GUI setup:** choose a strong password; when the offline recovery key is displayed, store it and acknowledge it. It allows recovery and setting a new password without replacing the DEK.
- **Login:** password-based unlocking is required before GUI construction and receiving services start. If unlocking fails, the application must remain closed (fail-closed).
- **Forgotten password:** use the GUI recovery procedure with the recovery key. Do not reinstall or delete persistent state to recover the account.
- **Attachments:** encrypted at rest inside the application store; an attachment saved/exported outside that store is a new readable file for anyone with access to its destination.
- **Real-world checks:** developer and VM self-send; developer → VM; VM → developer; attachments sent successfully. Three databases with non-plaintext headers in both environments; GSAT v1 store observed. **1844 passed** in the complete developer suite.
- **Limitations:** alternative CLI/bootstrap/receiving paths were under review at the documented checkpoint; backups and temporary remnants were not comprehensively assessed; no legacy migration or independent cryptographic audit.

## Sources and release

Repository: https://github.com/giulsign/GarlicSMTP.git. Reference baseline: commit `9bfc2f7`, documentation version `v0.1.0-alpha.1`. Do not claim `pyproject.toml`, the Git tag or distribution artifacts have been aligned without verification. `git clone` and `./install.sh` describe the known installation path; installing *exactly* the frozen baseline requires formalizing the tag/release and verifying package metadata first. Do not update or reinstall over real data without an agreed procedure.

**Destructive uninstallation, only when explicitly intended:** from the checkout root, `python3 -m install.uninstaller`, with `DELETE` confirmation; removes application data and the Onion identity while preserving the source checkout. Do not use this as a password reset.
