# Aplikacja MVP - AI Video Creator

## Główny problem

**Tworzenie profesjonalnych, długich (np. minimum 1-minutowych) filmów AI w sposób dobrze kontrolowany jest niemożliwe.**

- Brak narzędzia do generowania spójnych kontekstowo długich filmów wideo
- Trudność w formułowaniu promptów video
- Trudność w zachowaniu ciągłości narracyjnej między różnymi inferencjami generowania wideo z AI
- Generowanie video z AI często daje niezadowalające rezultaty
- Złożoność techniczna integracji różnych API (voice cloning, video generation, audio)
- Brak możliwości iteracyjnego poprawiania poszczególnych fragmentów

**Rozwiązanie:** Aplikacja webowa z Human-in-the-Loop (HITL), która umożliwia kontrolowaną generację filmów video z wykorzystaniem AI, gdzie użytkownik zatwierdza każdy segment przed przejściem do następnego.

---

## Najmniejszy zestaw funkcjonalności (MVP Scope)

### 1. Autentykacja użytkownika
- [ ] Logowanie przez Azure Entra ID (Microsoft Account)
- [ ] Ekran logowania z przyciskiem "Zaloguj się przez Microsoft"
- [ ] Zabezpieczenie dostępu do aplikacji

### 2. Upload i inicjalizacja projektu
- [ ] Formularz tworzenia nowego projektu wideo
- [ ] Upload pierwszego obrazu (first frame) z komputera użytkownika
- [ ] Upload sample audio do voice cloning
- [ ] Wprowadzenie story prompt (opis narracji/historii)
- [ ] Wybór długości docelowej (max 60 sekund)
- [ ] Wybór długości segmentu (6 lub 10 sekund)

### 3. AI Planning & Prompt Generation
- [ ] Automatyczne generowanie planu wideo przez OpenAI Agents SDK
- [ ] Supervisor Agent tworzy VideoPlan z segmentami
- [ ] Generowanie promptów video i narracji dla każdego segmentu
- [ ] Wyświetlanie propozycji promptów w UI

### 4. Human-in-the-Loop Workflow
- [ ] Wyświetlanie proponowanego prompta dla następnego segmentu
- [ ] Możliwość edycji/modyfikacji prompta przez użytkownika
- [ ] Przyciski: "Zatwierdź" / "Edytuj" / "Regeneruj"
- [ ] Oczekiwanie na zatwierdzenie przed rozpoczęciem generowania

### 5. Generowanie segmentów wideo
- [ ] Voice cloning z przesłanego audio (MiniMax API)
- [ ] Generowanie audio narracji z tekstu (MiniMax TTS)
- [ ] Generowanie wideo z first-frame + last-frame (MiniMax FL2V)
- [ ] Wyświetlanie statusu/postępu generowania
- [ ] Polling statusu async tasks

### 6. Podgląd i zatwierdzanie
- [ ] Podgląd wygenerowanego segmentu wideo
- [ ] Odsłuch wygenerowanego audio
- [ ] Przyciski: "Zatwierdź segment" / "Regeneruj"
- [ ] Wyświetlanie historii zatwierdzonych segmentów

### 7. Finalizacja
- [ ] Konkatenacja zatwierdzonych segmentów (FFmpeg)
- [ ] Muxowanie video + audio
- [ ] Download finalnego pliku wideo
- [ ] Podgląd finalnego wideo w aplikacji

### 8. Zarządzanie projektami (CRUD)
- [ ] Lista projektów użytkownika
- [ ] Szczegóły projektu (status, segmenty)
- [ ] Usuwanie projektu
- [ ] Kontynuowanie niedokończonego projektu

---

## Co NIE wchodzi w zakres MVP

### Wyłączone funkcjonalności:
1. **Zaawansowana edycja wideo** - cięcie, przycinanie, efekty specjalne
2. **Wiele głosów/narratorów** - tylko jeden sklonowany głos na projekt
3. **Muzyka w tle** - tylko narracja głosowa
4. **Kolaboracja** - jeden użytkownik per projekt
5. **Wersjonowanie** - brak historii zmian/wersji
6. **Eksport do różnych formatów** - tylko MP4
7. **Integracje zewnętrzne** - brak publikacji na social media
8. **Zaawansowane MCP servers** - rezygnacja z MCP na rzecz bezpośrednich API calls
9. **Batch processing** - jeden projekt na raz
10. **Customowe modele AI** - tylko domyślne modele MiniMax
11. **Watermarking** - brak znaku wodnego
12. **Analityka użycia** - podstawowa tylko
13. **Mobile app** - tylko web responsive
14. **Offline mode** - wymaga połączenia z internetem
15. **Custom storage providers** - tylko lokalne/podstawowe

### Decyzje architektoniczne wykluczające złożoność:
- **NIE używamy MCP servers** - bezpośrednie wywołania API MiniMax
- **NIE używamy message queues** - synchroniczny polling z async/await
- **NIE używamy mikrousług** - monolityczny backend
- **NIE używamy Redis/cache** - podstawowy state management
- **NIE używamy zaawansowanego ORM** - prostsze SQLite/PostgreSQL

---

## Kryteria sukcesu

### Metryki funkcjonalne:
| Metryka | Cel MVP | Sposób mierzenia |
|---------|---------|------------------|
| Widoczność statusu generowania | 100% | Użytkownik widzi: "w trakcie", "sukces", "błąd" |
| Satysfakcja użytkownika z segmentu | ≥ 50% | Stosunek zatwierdzonych do regenerowanych |
| Funkcjonalność frontendu | 100% | Wszystkie przepływy UI działają poprawnie |
| Testy E2E | 100% pass rate | CI/CD pipeline |

### Metryki techniczne:
| Metryka | Cel MVP | Sposób mierzenia |
|---------|---------|------------------|
| CI/CD pipeline | Przechodzi | GitHub Actions - build + testy |
| Integracja MiniMax API | Działa | Testy integracyjne z prawdziwym API |
| Integracja OpenAI API | Działa | Testy generowania planu |
| Azure Entra auth | Działa | Ręczny test logowania |
| Deploy na Azure | Działa | Aplikacja dostępna pod URL |

### Kryteria akceptacji użytkownika:
1. ✅ Użytkownik może się zalogować przez Microsoft Account
2. ✅ Użytkownik może załadować obraz i audio
3. ✅ Użytkownik widzi proponowane prompty od AI
4. ✅ Użytkownik może zatwierdzić lub edytować prompt
5. ✅ Użytkownik widzi postęp generowania wideo
6. ✅ Użytkownik może obejrzeć wygenerowany segment
7. ✅ Użytkownik może pobrać finalne wideo
8. ✅ Użytkownik może zarządzać swoimi projektami

### Definition of Done dla MVP:
- [ ] Wszystkie user stories zaimplementowane i przetestowane
- [ ] Testy E2E przechodzą pomyślnie
- [ ] CI/CD pipeline działa
- [ ] GitHub Environments skonfigurowane (dev, prod)
- [ ] Dokumentacja API dostępna
- [ ] Deploy na Azure działa
- [ ] Code review zakończony

---

## Tech Stack Summary

### Frontend - Verified Package Versions (January 2026)

#### Core:
| Package | Version | Description |
|---------|---------|-------------|
| `react` | `19.2.4` | Declarative UI library with hooks and concurrent features |
| `react-dom` | `19.2.4` | React DOM rendering engine for browser environments |
| `typescript` | `5.9.3` | Statically typed JavaScript superset with advanced type inference |
| `vite` | `7.3.1` | Next-generation frontend build tool with native ES modules and HMR |

#### Routing & State:
| Package | Version | Description |
|---------|---------|-------------|
| `react-router-dom` | `7.13.0` | Declarative routing library for React single-page applications |
| `@tanstack/react-query` | `5.90.20` | Powerful server state management with caching and synchronization |
| `@tanstack/react-query-devtools` | `5.91.3` | Development tools for debugging React Query state and cache |

#### Azure Authentication:
| Package | Version | Description |
|---------|---------|-------------|
| `@azure/msal-browser` | `5.1.0` | Microsoft Authentication Library core for browser-based SPAs |
| `@azure/msal-react` | `5.0.3` | React bindings for MSAL with hooks and context providers |

#### Styling:
| Package | Version | Description |
|---------|---------|-------------|
| `tailwindcss` | `4.1.18` | Utility-first CSS framework for rapid custom UI development |

#### HTTP Client:
| Package | Version | Description |
|---------|---------|-------------|
| `axios` | `1.13.4` | Promise-based HTTP client with request/response interceptors |

#### DevDependencies:
| Package | Version | Description |
|---------|---------|-------------|
| `@types/react` | `19.2.10` | TypeScript type definitions for React 19 API |
| `@types/react-dom` | `19.2.3` | TypeScript type definitions for React DOM 19 API |
| `@vitejs/plugin-react` | `5.1.2` | Official Vite plugin for React with Fast Refresh support |
| `eslint` | `9.39.2` | Pluggable static analysis tool for JavaScript and TypeScript |
| `prettier` | `3.8.1` | Opinionated code formatter with zero configuration |

#### Version Compatibility Matrix (verified January 2026):
| Dependency | Requires | Verified With |
|------------|----------|---------------|
| `@azure/msal-react` v5 | React 19 | ✅ react@19.2.4 |
| `@tanstack/react-query` v5 | React 18+ | ✅ react@19.2.4 |
| `react-router-dom` v7 | React 18+ | ✅ react@19.2.4 |
| `@vitejs/plugin-react` v5 | React 16.9+, Vite 6+ | ✅ react@19.2.4, vite@7.3.1 |
| `@types/react` v19 | TypeScript 4.7+ | ✅ typescript@5.9.3 |
| `tailwindcss` v4 | PostCSS 8+ | ✅ Built-in |

> **Note:** All versions sourced from npm registry. MSAL React v5 is the first version with official React 19 support.

### Backend:
- **Python 3.11+** with FastAPI
- **OpenAI Agents SDK** - AI orchestration and planning
- **MiniMax API** - Video/audio generation (direct API calls, NO MCP)
- **FFmpeg** - Media processing operations
- **SQLite/PostgreSQL** - Data persistence

### Infrastructure:
- **Azure App Service** - Backend hosting
- **Azure Static Web Apps** - Frontend hosting
- **Azure Entra ID** - Authentication provider
- **GitHub Actions** - CI/CD pipelines
- **Azure Blob Storage** (optional) - Media file storage

---

## Reference package.json

```json
{
  "name": "ai-video-creator-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^19.2.4",
    "react-dom": "^19.2.4",
    "react-router-dom": "^7.13.0",
    "@tanstack/react-query": "^5.90.20",
    "@azure/msal-browser": "^5.1.0",
    "@azure/msal-react": "^5.0.3",
    "axios": "^1.13.4",
    "tailwindcss": "^4.1.18"
  },
  "devDependencies": {
    "@tanstack/react-query-devtools": "^5.91.3",
    "@types/react": "^19.2.10",
    "@types/react-dom": "^19.2.3",
    "@vitejs/plugin-react": "^5.1.2",
    "typescript": "^5.9.3",
    "vite": "^7.3.1",
    "eslint": "^9.39.2",
    "prettier": "^3.8.1"
  }
}
```
