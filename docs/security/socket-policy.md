# Socket.dev Alert Policy

- **Block:** malware, typosquatting, dependency confusion, compromised
  ownership, confirmed high/critical vulnerabilities, or unexplained binary
  payloads.
- **Review:** shell/network access, `eval`/`exec`, install scripts, new native
  code, opaque archives, and AI-generated findings.
- **Monitor:** verified native scientific-library behaviour, established build
  behaviour, and informational popularity/maintainer signals.

Suppressions must identify the exact package version, artifact, SHA-256, rule,
evidence, owner, and expiry. Blanket suppressions for NumPy, SciPy, native code,
install scripts, or compressed archives are prohibited.
