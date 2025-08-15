# Launch Checklist

Security
- [ ] Rotate SECRET_KEY; store secrets in a vault
- [ ] Restrict CORS to production domains
- [ ] HTTPS/TLS termination (proxy/load balancer)

Platform
- [ ] Facebook app settings: valid domains, redirect URIs
- [ ] App Review plan; privacy policy + data deletion URL
- [ ] Per-agent OAuth (replace static page token)

Reliability
- [ ] Redis HA or managed Redis
- [ ] Health checks, logs, error tracking
- [ ] Backups and retention

Go-to-Market
- [ ] Pricing tiers and limits
- [ ] Onboarding guide and demo
- [ ] Feedback loop and success metrics
