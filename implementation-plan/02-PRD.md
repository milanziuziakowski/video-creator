# Product Requirements Document (PRD)
# AI Video Creator - 1-Minute Video Studio

**Document Version:** 1.0  
**Last Updated:** January 31, 2026  
**Author:** AI Architecture Design  
**Status:** Draft for Review

---

## 1. Executive Summary

### 1.1 Co budujemy i po co?

**AI Video Creator** to aplikacja webowa umożliwiająca tworzenie profesjonalnych, 1-minutowych filmów video z wykorzystaniem sztucznej inteligencji. Aplikacja łączy:
- Generowanie wideo AI (MiniMax Hailuo)
- Klonowanie głosu i syntezę mowy (MiniMax TTS)
- Inteligentne planowanie narracji (OpenAI Agents SDK)
- Human-in-the-Loop workflow dla kontroli jakości na każdym
- Sklejanie 6 lub 10-sekundowych klipów generowanych przez MiniMax
- Approval użytkownika przed każdą kolejną iteracją klipu mający na celu kontrolę poprawności i zachowanie spójnego całościowego video  

**Cel produktu:** Umożliwić użytkownikom tworzenie wysokiej jakości filmów AI z kontrolą nad każdym etapem procesu.

### 1.2 Jaki ból rozwiązujemy?

| Problem | Rozwiązanie |
|---------|-------------|
| Tworzenie spójnych segmentów wideo jest czasochłonne | OpenAI Supervisotr Agent automatycznie planuje i generuje prompty do segmentów z zachowaniem ciągłości |
| Brak kontroli nad jakością automatycznego generowania | Human-in-the-Loop pozwala zatwierdzać każdy segment |
| Złożoność techniczna integracji wielu narzędzi AI | Jedna zunifikowana aplikacja z intuicyjnym UI |
| Trudność w zachowaniu spójności narracyjnej | Supervisor Agent planuje całą narrację przed generowaniem |
| Brak profesjonalnej jakości głosu | Voice cloning z własnego sampla audio |

---

## 2. Stakeholders & Target Users

### 2.1 Primary Users
- **Entertainment Creators** - twórcy viralowych treści rozrywkowych (TikTok, Reels, Shorts)
- **Storytellers** - osoby wizualizujące opowiadania, historyjki i scenariusze
- **Social Media Users** - osoby tworzące content dla zabawy i znajomych
- **Streamers & YouTubers** - twórcy potrzebujący insertów i krótkich form wideo

### 2.2 User Personas

#### Persona 1: Storyteller Sarah
- **Rola:** Hobbyist Writer / Storyteller
- **Cel:** Wizualizacja własnych opowiadań i creepypast na YouTube
- **Ból:** Brak umiejętności animacji/wideo do zilustrowania historii
- **Oczekiwanie:** Spójność postaci i klimatu, łatwe dodawanie narracji

#### Persona 2: Creator Chris
- **Rola:** Content Creator na TikTok/YouTube Shorts
- **Cel:** Generowanie viralowych, zabawnych filmów rozrywkowych
- **Ból:** Wypalenie i czasochłonność manualnej edycji
- **Oczekiwanie:** Szybkość, kreatywne możliwości, wysoki potencjał viralowy

---

## 3. Functional Requirements

### 3.1 User Authentication (FR-AUTH)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-AUTH-01 | System musi obsługiwać logowanie przez OAuth2 z tokenami JWT | P0 |
| FR-AUTH-02 | System musi wyświetlać ekran logowania dla niezalogowanych użytkowników | P0 |
| FR-AUTH-03 | System musi przechowywać token sesji | P0 |
| FR-AUTH-04 | System musi obsługiwać wylogowanie | P0 |
| FR-AUTH-05 | System musi chronić wszystkie endpointy przed nieautoryzowanym dostępem | P0 |

### 3.2 Project Management (FR-PROJ)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-PROJ-01 | Użytkownik musi móc utworzyć nowy projekt wideo | P0 |
| FR-PROJ-02 | Użytkownik musi móc przeglądać listę swoich projektów | P0 |
| FR-PROJ-03 | Użytkownik musi móc otworzyć szczegóły projektu | P0 |
| FR-PROJ-04 | Użytkownik musi móc usunąć projekt | P1 |
| FR-PROJ-05 | System musi zapisywać stan projektu automatycznie | P0 |
| FR-PROJ-06 | Użytkownik musi móc kontynuować niedokończony projekt | P0 |

### 3.3 Media Upload (FR-UPLOAD)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-UPLOAD-01 | Użytkownik musi móc załadować obraz jako first frame | P0 |
| FR-UPLOAD-02 | System musi akceptować formaty: JPG, PNG, WEBP | P0 |
| FR-UPLOAD-03 | Użytkownik musi móc załadować audio sample do voice cloning | P0 |
| FR-UPLOAD-04 | System musi akceptować audio: MP3, WAV, M4A (10s-5min, <20MB) | P0 |
| FR-UPLOAD-05 | System musi walidować rozmiar i format plików | P0 |
| FR-UPLOAD-06 | System musi wyświetlać podgląd załadowanych plików | P1 |

### 3.4 AI Planning (FR-PLAN)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-PLAN-01 | Użytkownik musi móc wprowadzić story prompt | P0 |
| FR-PLAN-02 | System musi generować plan wideo (VideoPlan) przez AI | P0 |
| FR-PLAN-03 | System musi generować prompty dla każdego segmentu | P0 |
| FR-PLAN-04 | System musi generować tekst narracji dla każdego segmentu | P0 |
| FR-PLAN-05 | System musi wyświetlać wygenerowany plan użytkownikowi | P0 |
| FR-PLAN-06 | Użytkownik musi móc edytować wygenerowane prompty | P0 |

### 3.5 Human-in-the-Loop (FR-HITL)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-HITL-01 | System musi wyświetlać proponowany prompt przed generowaniem | P0 |
| FR-HITL-02 | Użytkownik musi zatwierdzić prompt przed rozpoczęciem generowania | P0 |
| FR-HITL-03 | Użytkownik musi móc edytować prompt przed zatwierdzeniem | P0 |
| FR-HITL-04 | System musi czekać na zatwierdzenie użytkownika | P0 |
| FR-HITL-05 | Użytkownik musi móc regenerować segment po obejrzeniu | P0 |
| FR-HITL-06 | System musi wyświetlać podgląd wygenerowanego segmentu | P0 |

### 3.6 Video/Audio Generation (FR-GEN)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-GEN-01 | System musi klonować głos z przesłanego audio | P0 |
| FR-GEN-02 | System musi generować audio narracji z tekstu | P0 |
| FR-GEN-03 | System musi generować wideo z first/last frame (FL2V) | P0 |
| FR-GEN-04 | System musi wyświetlać status generowania | P0 |
| FR-GEN-05 | System musi obsługiwać async polling statusu | P0 |
| FR-GEN-06 | System musi obsługiwać błędy generowania i retry | P1 |
| FR-GEN-07 | System musi akceptować URL lub Base64 dla first_frame_image | P0 |
| FR-GEN-08 | System musi akceptować URL lub Base64 dla last_frame_image | P0 |
| FR-GEN-09 | System musi wspierać komendy ruchu kamery w promptach ([Zoom in], [Pan left], etc.) | P1 |
| FR-GEN-10 | System musi wspierać rozdzielczości 768P i 1080P dla FL2V | P0 |
| FR-GEN-11 | System musi wspierać duration 6s i 10s dla FL2V | P0 |
| FR-GEN-12 | System musi obsługiwać prompt_optimizer flag dla precyzyjnej kontroli | P1 |

### 3.6.1 First & Last Frame Video Generation (FR-FL2V)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-FL2V-01 | Użytkownik może uploadować first_frame_image (JPG, PNG, WEBP) | P0 |
| FR-FL2V-02 | Użytkownik może uploadować last_frame_image (JPG, PNG, WEBP) | P0 |
| FR-FL2V-03 | System musi walidować: short side > 300px, aspect ratio 2:5 - 5:2 | P0 |
| FR-FL2V-04 | System musi walidować rozmiar pliku < 20MB | P0 |
| FR-FL2V-05 | Rozdzielczość wideo jest determinowana przez first_frame_image | P0 |
| FR-FL2V-06 | Last frame jest automatycznie przycinany do rozmiaru first frame | P0 |
| FR-FL2V-07 | System używa modelu MiniMax-Hailuo-02 dla FL2V | P0 |
| FR-FL2V-08 | Prompt może zawierać do 2000 znaków | P0 |

### 3.7 Finalization (FR-FINAL)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-FINAL-01 | System musi konkatenować zatwierdzone segmenty wideo | P0 |
| FR-FINAL-02 | System musi konkatenować audio narracji | P0 |
| FR-FINAL-03 | System musi muxować video + audio w finalny plik | P0 |
| FR-FINAL-04 | Użytkownik musi móc pobrać finalny plik MP4 | P0 |
| FR-FINAL-05 | Użytkownik musi móc obejrzeć finalne wideo w aplikacji | P0 |

---

## 4. Non-Functional Requirements

### 4.1 Performance (NFR-PERF)

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-PERF-01 | Response time dla API (non-generation) | < 2 seconds |
| NFR-PERF-02 | Czas generowania pojedynczego segmentu | < 5 minutes |
| NFR-PERF-03 | Czas finalizacji (concat + mux) | < 2 minutes |
| NFR-PERF-04 | Maksymalny rozmiar pliku upload | 20 MB |
| NFR-PERF-05 | Obsługa jednoczesnych użytkowników | 10+ |

### 4.2 Security (NFR-SEC)

| ID | Requirement |
|----|-------------|
| NFR-SEC-01 | Wszystkie dane muszą być przesyłane przez HTTPS |
| NFR-SEC-02 | Autentykacja musi używać OAuth2 z tokenami JWT |
| NFR-SEC-03 | API keys muszą być przechowywane w zmiennych środowiskowych |
| NFR-SEC-04 | Użytkownicy mogą widzieć tylko swoje projekty |
| NFR-SEC-05 | Sesje muszą wygasać po 24h nieaktywności |

### 4.3 Reliability (NFR-REL)

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-REL-01 | Uptime aplikacji | > 99% |
| NFR-REL-02 | Error rate | < 5% |
| NFR-REL-03 | Data persistence | Zero data loss |
| NFR-REL-04 | Recovery time | < 5 minutes |

### 4.4 Usability (NFR-USE)

| ID | Requirement |
|----|-------------|
| NFR-USE-01 | Interfejs musi być responsywny (mobile-friendly) |
| NFR-USE-02 | Wszystkie akcje muszą mieć feedback wizualny |
| NFR-USE-03 | Błędy muszą być komunikowane zrozumiale |
| NFR-USE-04 | Workflow musi być intuicyjny (max 5 kroków) |

---

## 5. User Stories

### Epic 1: Authentication & Authorization

#### US-1.1: Login
```
JAKO użytkownik
CHCĘ zalogować się przez Microsoft Account
ABY uzyskać dostęp do aplikacji

Kryteria akceptacji:
- Widzę przycisk "Zaloguj się przez Microsoft"
- Po kliknięciu jestem przekierowany do strony logowania Microsoft
- Po zalogowaniu wracam do aplikacji jako zalogowany użytkownik
- Widzę moje imię/email w nagłówku aplikacji
```

#### US-1.2: Logout
```
JAKO zalogowany użytkownik
CHCĘ się wylogować
ABY zabezpieczyć swoje konto

Kryteria akceptacji:
- Widzę przycisk/opcję wylogowania
- Po wylogowaniu wracam do ekranu logowania
- Nie mam dostępu do chronionych zasobów
```

### Epic 2: Project Management

#### US-2.1: Create Project
```
JAKO użytkownik
CHCĘ utworzyć nowy projekt wideo
ABY rozpocząć tworzenie filmu

Kryteria akceptacji:
- Widzę przycisk "Nowy projekt"
- Mogę wprowadzić nazwę projektu
- Mogę wybrać długość wideo (max 60s)
- Mogę wybrać długość segmentu (6s lub 10s)
- Projekt jest zapisywany i pojawia się na liście
```

#### US-2.2: Upload Media
```
JAKO użytkownik
CHCĘ załadować obraz i audio
ABY dostarczyć materiały początkowe

Kryteria akceptacji:
- Mogę przeciągnąć lub wybrać plik obrazu
- Widzę podgląd załadowanego obrazu
- Mogę przeciągnąć lub wybrać plik audio
- Widzę informację o załadowanym audio (czas trwania)
- System waliduje format i rozmiar plików
```

### Epic 3: AI Planning

#### US-3.1: Generate Plan
```
JAKO użytkownik
CHCĘ wprowadzić opis historii
ABY AI wygenerowało plan wideo

Kryteria akceptacji:
- Widzę pole tekstowe do wprowadzenia story prompt
- Po zatwierdzeniu widzę loading indicator
- Otrzymuję plan z segmentami i promptami
- Widzę tytuł, prompty video i teksty narracji
```

#### US-3.2: Review & Edit Plan
```
JAKO użytkownik
CHCĘ przejrzeć i edytować wygenerowany plan
ABY dostosować go do moich potrzeb

Kryteria akceptacji:
- Widzę listę wszystkich segmentów
- Mogę kliknąć na segment aby zobaczyć szczegóły
- Mogę edytować prompt video
- Mogę edytować tekst narracji
- Zmiany są zapisywane
```

### Epic 4: Human-in-the-Loop Generation

#### US-4.1: Approve Prompt
```
JAKO użytkownik
CHCĘ zobaczyć proponowany prompt przed generowaniem
ABY mieć kontrolę nad wynikiem

Kryteria akceptacji:
- Widzę proponowany prompt dla aktualnego segmentu
- Widzę proponowany tekst narracji
- Mam przycisk "Zatwierdź i generuj"
- Mam przycisk "Edytuj"
- Generowanie nie rozpoczyna się bez zatwierdzenia
```

#### US-4.2: Monitor Generation
```
JAKO użytkownik
CHCĘ widzieć postęp generowania
ABY wiedzieć ile to potrwa

Kryteria akceptacji:
- Widzę pasek postępu lub status
- Widzę szacowany czas ukończenia
- Widzę komunikat o błędzie jeśli wystąpi
- Mogę anulować generowanie (opcjonalnie)
```

#### US-4.3: Review Segment
```
JAKO użytkownik
CHCĘ obejrzeć wygenerowany segment
ABY zdecydować czy go zatwierdzić

Kryteria akceptacji:
- Widzę player video z wygenerowanym segmentem
- Mogę odtworzyć audio narracji
- Mam przycisk "Zatwierdź segment"
- Mam przycisk "Regeneruj"
- Zatwierdzenie przenosi mnie do następnego segmentu
```

### Epic 5: Finalization

#### US-5.1: Finalize Video
```
JAKO użytkownik
CHCĘ sfinalizować projekt
ABY otrzymać gotowy film

Kryteria akceptacji:
- Po zatwierdzeniu wszystkich segmentów widzę opcję finalizacji
- Widzę postęp składania filmu
- Po zakończeniu widzę player z finalnym wideo
- Mam przycisk "Pobierz MP4"
```

#### US-5.2: Download Video
```
JAKO użytkownik
CHCĘ pobrać finalny film
ABY używać go poza aplikacją

Kryteria akceptacji:
- Klikam przycisk "Pobierz"
- Plik MP4 jest pobierany na mój komputer
- Jakość wideo jest zachowana
```

---

## 6. Success Metrics (KPIs)

### 6.1 Engagement Metrics
- **Project Creation Rate:** Liczba nowych projektów / tydzień
- **Completion Rate:** % projektów doprowadzonych do finalizacji
- **Return Rate:** % użytkowników powracających w ciągu 7 dni

### 6.2 Quality Metrics
- **Regeneration Rate:** % segmentów wymagających regeneracji (cel: < 30%)
- **Error Rate:** % nieudanych generowań (cel: < 5%)
- **User Satisfaction:** Ankieta satysfakcji (cel: > 4/5)

### 6.3 Technical Metrics
- **Average Generation Time:** Średni czas generowania segmentu
- **Finalization Success Rate:** % udanych finalizacji
- **API Response Time:** P95 response time < 2s

---

## 7. Milestones & Timeline

### Phase 1: Foundation (Week 1-2)
- [x] Setup projektu React + TypeScript
- [x] Konfiguracja OAuth2 JWT Auth
- [x] Podstawowy backend FastAPI
- [x] Database schema

### Phase 2: Core Features (Week 3-4)
- [ ] Upload media
- [ ] AI Planning (OpenAI Agents SDK)
- [ ] HITL Workflow UI

### Phase 3: Generation (Week 5-6)
- [ ] MiniMax API integration
- [ ] Video generation pipeline
- [ ] Polling & status

### Phase 4: Finalization (Week 7)
- [ ] FFmpeg operations
- [ ] Download functionality
- [ ] E2E testing

### Phase 5: Deploy (Week 8)
- [ ] CI/CD pipeline
- [ ] Azure deployment
- [ ] Documentation

---

## 8. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| MiniMax API downtime | Medium | High | Retry logic, user communication |
| High generation costs | High | Medium | Rate limiting, cost monitoring |
| Slow generation time | High | Medium | Progress feedback, async UX |
| OAuth2 JWT config issues | Low | High | Thorough testing, documentation |
| FFmpeg compatibility | Low | Medium | Docker containerization |

---

## 9. Out of Scope (Explicit Exclusions)

Dla jasności, poniższe funkcjonalności **NIE** są częścią tego PRD:
- Multi-language support
- Team collaboration
- Advanced video editing
- Social media publishing
- Mobile native apps
- Offline functionality
- Custom AI model training
- White-label solution

---

## 10. Appendix

### A. Glossary
- **HITL:** Human-in-the-Loop - proces z udziałem człowieka
- **FL2V:** First-Last-Frame-to-Video - technika generowania wideo z użyciem pierwszej i ostatniej klatki
- **Voice Cloning:** Klonowanie głosu z próbki audio
- **TTS:** Text-to-Speech - synteza mowy z tekstu
- **Segment:** Pojedynczy fragment wideo (6 lub 10 sekund)
- **Camera Commands:** Komendy sterowania kamerą w formacie [command] np. [Zoom in], [Pan left], [Push in]
- **Prompt Optimizer:** Funkcja automatycznej optymalizacji promptu przez MiniMax API

### B. Related Documents
- [01-MVP-DEFINITION.md](./01-MVP-DEFINITION.md)
- [03-ARCHITECTURE.md](./03-ARCHITECTURE.md)
- [04-BACKEND-IMPLEMENTATION.md](./04-BACKEND-IMPLEMENTATION.md)
- [05-FRONTEND-IMPLEMENTATION.md](./05-FRONTEND-IMPLEMENTATION.md)
