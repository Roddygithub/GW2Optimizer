# 📘 GW2Optimizer API Guide

**Version**: 1.0.0  
**Base URL**: `http://localhost:8000/api/v1`  
**Documentation Interactive**: `http://localhost:8000/docs`

---

## 🔐 Authentication

### Register
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "player123",
  "password": "SecurePass!123"
}
```

**Response 201**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "player123",
    "is_active": true,
    "is_verified": false
  }
}
```

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass!123"
}
```

### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Logout
```http
POST /auth/logout
Authorization: Bearer {access_token}
```

---

## 🤖 AI Endpoints

### 1. Recommend Build
```http
POST /ai/recommend-build
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "profession": "Guardian",
  "role": "Support",
  "game_mode": "WvW",
  "context": "Looking for a support build for zerging"
}
```

**Response 200**:
```json
{
  "build_name": "Firebrand Support",
  "description": "High boon uptime support build...",
  "synergies": ["Quickness", "Stability", "Aegis"],
  "traits": {
    "line1": "Radiance",
    "line2": "Honor",
    "line3": "Firebrand"
  },
  "equipment": {
    "armor": "Harrier's",
    "weapons": "Mace/Shield + Staff",
    "runes": "Rune of the Monk"
  }
}
```

### 2. Analyze Team Synergy
```http
POST /ai/analyze-team-synergy
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "professions": ["Guardian", "Warrior", "Mesmer", "Necromancer", "Ranger"],
  "game_mode": "WvW"
}
```

**Response 200**:
```json
{
  "synergy_score": 85,
  "strengths": [
    "High boon coverage",
    "Good crowd control",
    "Balanced damage and support"
  ],
  "weaknesses": [
    "Limited ranged damage",
    "Vulnerable to condition pressure"
  ],
  "suggestions": [
    "Consider adding a Scourge for condition cleanse",
    "Guardian should focus on stability uptime"
  ]
}
```

### 3. Optimize Team
```http
POST /ai/optimize-team
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "current_composition": ["Guardian", "Warrior", "Thief", "Ranger", "Elementalist"],
  "objectives": ["maximize_boons", "improve_cc"],
  "game_mode": "Raids",
  "max_changes": 2
}
```

**Response 200**:
```json
{
  "optimized_composition": ["Guardian", "Warrior", "Mesmer", "Ranger", "Elementalist"],
  "changes": [
    {
      "from": "Thief",
      "to": "Mesmer",
      "reason": "Better boon support and crowd control"
    }
  ],
  "improvement_score": 15.5,
  "rationale": "Replacing Thief with Mesmer significantly improves boon coverage..."
}
```

### 4. Build Optimization Workflow
```http
POST /ai/workflow/build-optimization
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "profession": "Warrior",
  "role": "DPS",
  "game_mode": "Fractals",
  "team_composition": ["Guardian", "Warrior", "Mesmer", "Ranger", "Elementalist"],
  "optimization_iterations": 2
}
```

**Response 200**:
```json
{
  "workflow_id": "uuid",
  "status": "completed",
  "result": {
    "final_build": {
      "name": "Berserker DPS",
      "traits": {...},
      "skills": [...],
      "equipment": {...}
    },
    "synergy_analysis": {...},
    "optimization_history": [...]
  },
  "execution_time": 2.5
}
```

### 5. Team Analysis Workflow
```http
POST /ai/workflow/team-analysis
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "professions": ["Guardian", "Warrior", "Mesmer", "Necromancer", "Ranger"],
  "game_mode": "WvW",
  "optimize": true,
  "max_changes": 3
}
```

**Response 200**:
```json
{
  "workflow_id": "uuid",
  "status": "completed",
  "result": {
    "analysis": {
      "synergy_score": 82,
      "strengths": [...],
      "weaknesses": [...]
    },
    "optimized_composition": [...],
    "suggestions": [...]
  },
  "execution_time": 3.2
}
```

### 6. AI Status
```http
GET /ai/status
Authorization: Bearer {access_token}
```

**Response 200**:
```json
{
  "status": "operational",
  "ollama_connected": true,
  "model": "mistral:latest",
  "agents": {
    "recommender": "ready",
    "synergy": "ready",
    "optimizer": "ready"
  },
  "workflows": {
    "build_optimization": "ready",
    "team_analysis": "ready",
    "learning": "ready"
  }
}
```

---

## 🏗️ Build Endpoints

### Create Build
```http
POST /builds
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "My Guardian Build",
  "profession": "Guardian",
  "role": "Support",
  "game_mode": "WvW",
  "description": "Firebrand support for WvW",
  "traits": {...},
  "skills": [...],
  "equipment": {...},
  "is_public": false
}
```

### List Builds
```http
GET /builds?profession=Guardian&role=Support&limit=20
Authorization: Bearer {access_token}
```

### Get Build
```http
GET /builds/{build_id}
Authorization: Bearer {access_token}
```

### Update Build
```http
PUT /builds/{build_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Updated Build Name",
  "description": "New description"
}
```

### Delete Build
```http
DELETE /builds/{build_id}
Authorization: Bearer {access_token}
```

---

## 👥 Team Endpoints

### Create Team
```http
POST /teams
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "WvW Zerg Squad",
  "game_mode": "WvW",
  "description": "Main zerg composition",
  "slots": [
    {
      "build_id": "uuid",
      "slot_number": 1,
      "player_name": "Player1"
    }
  ],
  "is_public": false
}
```

### List Teams
```http
GET /teams?game_mode=WvW&limit=20
Authorization: Bearer {access_token}
```

### Get Team
```http
GET /teams/{team_id}
Authorization: Bearer {access_token}
```

### Add Build to Team
```http
POST /teams/{team_id}/builds
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "build_id": "uuid",
  "slot_number": 2,
  "player_name": "Player2"
}
```

### Remove Build from Team
```http
DELETE /teams/{team_id}/builds/{slot_id}
Authorization: Bearer {access_token}
```

---

## 💬 Chat Endpoint

### Send Message
```http
POST /chat
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "message": "What's the best Guardian build for WvW?",
  "context": {
    "profession": "Guardian",
    "game_mode": "WvW"
  }
}
```

**Response 200**:
```json
{
  "response": "For WvW, I recommend a Firebrand support build...",
  "suggestions": [
    "View Firebrand builds",
    "Analyze team composition"
  ]
}
```

---

## 📊 Learning Endpoints

### Submit Feedback
```http
POST /learning/feedback
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "build_id": "uuid",
  "rating": 5,
  "comment": "Excellent build for raids",
  "tags": ["effective", "fun"]
}
```

### Get Statistics
```http
GET /learning/stats
Authorization: Bearer {access_token}
```

---

## 🏥 Health Check

```http
GET /health
```

**Response 200**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-20T17:30:00Z",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected",
  "ollama": "connected"
}
```

---

## 🔒 Security Headers

All responses include:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`
- `X-Request-ID: {uuid}`
- `X-Process-Time: {ms}`

---

## ⚠️ Error Responses

### 400 Bad Request
```json
{
  "error_code": "VALIDATION_ERROR",
  "detail": "One or more validation errors occurred.",
  "fields": {
    "profession": "Invalid profession. Must be one of: Guardian, Warrior..."
  },
  "correlation_id": "uuid"
}
```

### 401 Unauthorized
```json
{
  "error_code": "INVALID_CREDENTIALS",
  "detail": "Invalid credentials",
  "correlation_id": "uuid"
}
```

### 403 Forbidden
```json
{
  "error_code": "ACCOUNT_LOCKED",
  "detail": "Account is locked due to too many failed login attempts",
  "correlation_id": "uuid"
}
```

### 404 Not Found
```json
{
  "error_code": "NOT_FOUND",
  "detail": "Build not found",
  "correlation_id": "uuid"
}
```

### 429 Too Many Requests
```json
{
  "error_code": "RATE_LIMIT_EXCEEDED",
  "detail": "Too many requests. Please try again later.",
  "correlation_id": "uuid"
}
```

### 500 Internal Server Error
```json
{
  "error_code": "INTERNAL_SERVER_ERROR",
  "detail": "An unexpected error occurred. Please contact support.",
  "correlation_id": "uuid"
}
```

### 503 Service Unavailable
```json
{
  "error_code": "AI_SERVICE_UNAVAILABLE",
  "detail": "AI service is temporarily unavailable",
  "correlation_id": "uuid"
}
```

---

## 📝 Rate Limiting

- **Authentication endpoints**: 5 requests/minute
- **AI endpoints**: 10 requests/minute
- **Other endpoints**: 60 requests/minute

---

## 🔑 Valid Values

### Professions
`Guardian`, `Revenant`, `Warrior`, `Engineer`, `Ranger`, `Thief`, `Elementalist`, `Mesmer`, `Necromancer`

### Roles
`DPS`, `Support`, `Tank`, `Hybrid`, `Healer`, `Boon`

### Game Modes
`PvE`, `PvP`, `WvW`, `Raids`, `Fractals`, `Strikes`

### Optimization Objectives
`maximize_boons`, `maximize_damage`, `maximize_survivability`, `balance_damage`, `improve_cc`, `optimize_synergy`

---

## 📚 Examples

### Complete Build Creation Flow
```bash
# 1. Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"player123","password":"SecurePass!123"}'

# 2. Get AI recommendation
curl -X POST http://localhost:8000/api/v1/ai/recommend-build \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"profession":"Guardian","role":"Support","game_mode":"WvW"}'

# 3. Create build
curl -X POST http://localhost:8000/api/v1/builds \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Firebrand Support","profession":"Guardian","role":"Support","game_mode":"WvW"}'

# 4. List your builds
curl -X GET "http://localhost:8000/api/v1/builds?profession=Guardian" \
  -H "Authorization: Bearer {token}"
```

---

**Documentation générée le**: 20 Octobre 2025  
**Pour plus d'informations**: Consultez `/docs` pour la documentation interactive Swagger
