# Security policy

Please do not file public issues for suspected vulnerabilities. Email the repository maintainer with reproduction steps, affected version, and impact. We will acknowledge reports promptly and coordinate a fix before disclosure.

RequestBinX intentionally handles sensitive request data. Deployers must configure TLS, a unique JWT secret, network isolation for PostgreSQL/Redis, and retention limits.
