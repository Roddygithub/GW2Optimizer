# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 1.1.x   | :white_check_mark: |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within GW2Optimizer, please send an email to the maintainers via GitHub. All security vulnerabilities will be promptly addressed.

**Please do not report security vulnerabilities through public GitHub issues.**

### What to include in your report

* Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
* Full paths of source file(s) related to the manifestation of the issue
* The location of the affected source code (tag/branch/commit or direct URL)
* Any special configuration required to reproduce the issue
* Step-by-step instructions to reproduce the issue
* Proof-of-concept or exploit code (if possible)
* Impact of the issue, including how an attacker might exploit the issue

### Response Timeline

* We will acknowledge receipt of your vulnerability report within 48 hours
* We will provide a detailed response within 7 days
* We will work with you to understand and resolve the issue
* We will notify you when the issue is fixed

## Security Best Practices

When using GW2Optimizer:

### API Keys
* Never commit API keys or secrets to the repository
* Use environment variables for sensitive configuration
* Rotate API keys regularly

### Authentication
* Use strong passwords (minimum 12 characters)
* Enable two-factor authentication when available
* Never share authentication tokens

### Deployment
* Always use HTTPS in production
* Keep dependencies up to date
* Use the latest stable version
* Follow the security headers configuration in production

### Database
* Use strong database passwords
* Restrict database access to necessary services only
* Regular backups
* Encrypt sensitive data at rest

## Known Security Considerations

### Content Security Policy (CSP)
* Development mode has relaxed CSP for Swagger/ReDoc
* Production mode enforces strict CSP
* Configure CSP appropriately for your deployment

### CORS
* Configure CORS origins appropriately
* Do not use wildcard (*) in production
* Restrict to trusted domains only

### Rate Limiting
* API endpoints have rate limiting enabled
* Adjust limits based on your infrastructure
* Monitor for abuse patterns

## Known risk: ecdsa dependency
* **Status**: upstream vulnerability reported; no fixed version publicly available at the time of writing.
* **Impact**: limited in our context. We rely on `python-jose[cryptography]` and do not use ECDSA directly in application flows.
* **Mitigation**:
  * Continuous monitoring via Dependabot and `pip-audit`.
  * Re-evaluate monthly or when upstream releases a patched version.
* **Decision**: risk accepted (temporary), documented and tracked.

## Security Updates

Security updates will be released as patch versions (e.g., 1.1.1) and announced via:
* GitHub Security Advisories
* CHANGELOG.md
* GitHub Releases

## Responsible Disclosure

We kindly ask you to:
* Give us reasonable time to fix the issue before public disclosure
* Make a good faith effort to avoid privacy violations and data destruction
* Not exploit the vulnerability beyond what is necessary to demonstrate it

## Contact

For security concerns, please create a private security advisory on GitHub or contact the maintainers directly.

---

**Last Updated**: 2025-11-03  
**Version**: 1.1.1
