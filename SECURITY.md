# GarlicSMTP Security Policy

GarlicSMTP is security-sensitive software designed to transport
email through Tor Onion Services.

Security and privacy reports are taken seriously.

## Project Status

GarlicSMTP is currently alpha software.

It has not undergone an independent professional security audit and
must not be considered a guarantee of anonymity, confidentiality,
integrity, or resistance to endpoint compromise.

Users should evaluate the risks of their environment and threat
model before relying on GarlicSMTP for sensitive communications.

## Reporting a Vulnerability

Please do not publicly disclose a suspected security vulnerability
before the maintainer has had a reasonable opportunity to
investigate it.

Security reports may be sent privately to:

giulisign@gmail.com

Please include, where possible:

- the affected GarlicSMTP version or commit;
- the affected component;
- a description of the vulnerability;
- steps required to reproduce it;
- the potential security or privacy impact;
- relevant logs or diagnostic information, after removing secrets
  and personally identifying information;
- any proposed mitigation or patch.

Do not include private Onion Service keys, authentication cookies,
passwords, private cryptographic keys, or other credentials in a
security report.

## Scope

Examples of issues considered security-relevant include:

- disclosure of a user's network address;
- bypass of intended Tor routing;
- unintended clearnet connections;
- Onion Service identity disclosure;
- authentication or authorization bypass;
- remote code execution;
- command or protocol injection;
- unsafe message parsing;
- unauthorized mailbox access;
- disclosure of message contents or metadata;
- insecure storage of cryptographic material;
- signature or encryption verification failures;
- vulnerabilities that materially weaken GarlicSMTP's intended
  privacy or anonymity properties.

## Third-Party Vulnerabilities

GarlicSMTP depends on third-party software, including Tor, Python,
Qt/PySide6, and other libraries.

A vulnerability originating entirely in a third-party component
should normally also be reported to that component's upstream
security team.

Reports are still welcome when a third-party vulnerability is
exposed or made materially worse by the way GarlicSMTP integrates
that component.

## Tor and Anonymity

GarlicSMTP's use of Tor Onion Services can reduce exposure of the
network locations of communicating endpoints.

This does not provide absolute anonymity.

Security can still be affected by, among other things:

- endpoint compromise;
- operating-system compromise;
- malicious dependencies;
- traffic analysis and correlation;
- application-level metadata;
- persistent pseudonymous Onion Service identities;
- unsafe logging;
- user configuration;
- cryptographic implementation errors;
- disclosure of locally stored messages or keys.

Tor cannot protect information that is compromised at an endpoint
before entering or after leaving the Tor-protected communication
path.

## Security-Sensitive Data

GarlicSMTP installations may contain sensitive material including:

- Onion Service private identity keys;
- Tor authentication material;
- queued messages;
- stored mailbox messages;
- sender and recipient identifiers;
- message metadata;
- application configuration.

Such material should not be committed to source control or included
in public bug reports.

## Supported Versions

Until GarlicSMTP reaches a stable release, security fixes are
provided primarily for the current development version.

Older commits and development snapshots may contain known or
unknown vulnerabilities.

## Responsible Disclosure

The maintainer will make a reasonable effort to:

1. acknowledge credible vulnerability reports;
2. investigate their impact;
3. develop or coordinate a correction where appropriate;
4. avoid unnecessary disclosure of reporter information;
5. publish security information when doing so is appropriate for
   protecting users.

No specific response or remediation time is guaranteed.

## Security Research

Good-faith security research intended to improve GarlicSMTP is
welcome when performed lawfully and without intentionally harming
other users, systems, or networks.

Testing should preferably be performed against systems and Onion
Services controlled by the researcher.

## No Security Warranty

GarlicSMTP is provided under the warranty and liability provisions
of its applicable license.

Nothing in this security policy constitutes a warranty, guarantee,
or representation that GarlicSMTP is secure, anonymous, or suitable
for any particular threat model.
