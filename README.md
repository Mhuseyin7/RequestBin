# RequestBinX

> Self-hosted webhook inspection, HTTP request capture ve API debugging platform.

**RequestBinX**, developers için tasarlanmış open-source bir developer tool'dur. Geçici veya kalıcı endpoint oluşturur; gelen webhook ve HTTP request'lerini canlı olarak yakalamanı, incelemeni, replay etmeni ve integration problemlerini hızlıca debug etmeni sağlar.

Bu software **[MuhammedKoca.com.tr](https://muhammedkoca.com.tr)** tarafından geliştirilmiştir ve open-source olarak paylaşılmaktadır.

## Neden RequestBinX?

Bir payment provider, CRM, form service veya kendi backend'in webhook gönderdiğinde; payload'ın gerçekten ne içerdiğini, hangi header'ların geldiğini veya neden integration'ın başarısız olduğunu görmek istersin. RequestBinX bunun için private bir receive URL oluşturur ve her incoming request'i canlı inspector ekranında gösterir.

- Live request feed ve WebSocket updates
- JSON, XML, plain text, form-data ve binary-safe body capture
- Headers, query parameters, cookies, IP, content type ve body size inspection
- Public hedeflere SSRF-protected request replay
- Sensitive header redaction (`Authorization`, `Cookie`, `X-API-Key` vb.)
- PostgreSQL persistence, filesystem body storage ve automatic retention cleanup
- Docker Compose ile self-hosted deployment

## Quick Start

### Prerequisites

- Docker Desktop ve Docker Compose

### Run locally

Önce environment file oluştur:

```powershell
Copy-Item .env.example .env
notepad .env
```

`.env` dosyasındaki `JWT_SECRET` değerini minimum 32 karakterlik random bir secret ile değiştir. Ardından stack'i başlat:

```powershell
docker compose up --build
```

Browser'dan aç:

| Service | URL |
| --- | --- |
| Web application | http://localhost:3000 |
| API documentation / OpenAPI | http://localhost:8000/docs |
| Health check | http://localhost:8000/healthz |

## Usage Flow

1. `http://localhost:3000` üzerinden account oluştur.
2. **New endpoint** ile bir bin oluştur.
3. Ekrandaki `/h/...` receive URL'sini kopyala.
4. Test request gönder:

```powershell
curl.exe -X POST "http://localhost:8000/h/YOUR_ENDPOINT_TOKEN" `
  -H "Content-Type: application/json" `
  -d "{\"event\":\"payment.completed\",\"order_id\":8412}"
```

5. Endpoint page'de request anlık görünür. Body, headers, query, cookies ve raw request bilgilerini inspect edebilirsin.
6. **Replay** ile request'i sadece güvenli/public bir target URL'ye tekrar gönderebilirsin.

## Architecture

```text
Next.js Web ── REST / WebSocket ── FastAPI API ── PostgreSQL
                                     │
                                     ├── filesystem body storage
                                     ├── retention worker
                                     └── Redis service layer
```

| Component | Technology | Responsibility |
| --- | --- | --- |
| Web | Next.js, React, TypeScript, Tailwind | Dashboard ve live inspector UI |
| API | FastAPI, SQLAlchemy, Pydantic | Auth, endpoint management, capture, replay |
| Database | PostgreSQL | Request metadata ve application data |
| Storage | Filesystem abstraction | Large/raw request body storage |
| Worker | Python async worker | Expired endpoint/body cleanup |
| Infrastructure | Docker Compose, Redis | Local/self-hosted deployment foundation |

## Security

RequestBinX sensitive webhook data işleyebilir. Bu nedenle:

- Password'ler Argon2id ile hash edilir.
- Endpoint token'ları cryptographically random üretilir; sequential ID kullanılmaz.
- Request body filename'ları user input'tan türetilmez.
- Common secret headers UI response'larında masked olarak döner.
- Replay, localhost, private IP, link-local address ve cloud metadata target'larını default olarak engeller.
- Redirect takip edilmez; DNS resolution target validation ile yapılır.

Production ortamında TLS reverse proxy kullanın, güçlü bir `JWT_SECRET` tanımlayın, PostgreSQL/Redis'i public network'e açmayın ve data retention politikanızı belirleyin.

> `ALLOW_UNSAFE_OUTBOUND=true` yalnızca tamamen güvenilir internal self-hosted environment'larda kullanılmalıdır.

## Development

### API

```powershell
cd api
pip install -r requirements.txt
pytest
```

### Web

```powershell
cd web
npm install
npm run typecheck
npm run build
```

## Project Status

Bu repository aktif bir open-source foundation'dır. Mevcut release; authentication, endpoint creation, request capture, realtime inspector, replay security ve retention worker içerir. Forwarding rules, organization/RBAC, API keys, distributed rate limiting, search/compare/export gibi gelişmiş modules roadmap kapsamındadır.

## Contributing

Contribution'lar memnuniyetle karşılanır. Pull request açmadan önce API tests ve web typecheck/build komutlarını çalıştırın. Secret, production payload veya credential commit etmeyin.

Detaylar için [CONTRIBUTING.md](CONTRIBUTING.md) dosyasına bakın. Security issue'ları public issue olarak paylaşmak yerine [SECURITY.md](SECURITY.md) içindeki süreci izleyin.

## License

MIT License altında yayınlanmıştır. Detaylar için [LICENSE](LICENSE).

---

Made with care by [MuhammedKoca.com.tr](https://muhammedkoca.com.tr) · Open source for developers.
