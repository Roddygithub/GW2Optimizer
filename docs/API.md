# API Documentation

Base URL: `http://localhost:8000/api/v1`

## Health Endpoints

### GET `/health`
Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "GW2Optimizer API",
  "version": "1.0.0"
}
```

### GET `/health/ollama`
Check Ollama service status.

## Chat Endpoints

### POST `/chat`
Send a message to the AI assistant.

**Request:**
```json
{
  "message": "Create a zerg composition for 25 players",
  "conversation_history": [],
  "context": null
}
```

**Response:**
```json
{
  "response": "AI response text...",
  "suggestions": ["Suggestion 1", "Suggestion 2"],
  "builds_mentioned": [],
  "action_required": "optimize_team"
}
```

## Build Endpoints

### POST `/builds`
Create a new build.

**Request:**
```json
{
  "profession": "Guardian",
  "game_mode": "zerg",
  "role": "support",
  "gw2skill_url": "http://gw2skills.net/...",
  "custom_requirements": "High boon duration"
}
```

**Response:**
```json
{
  "build": { /* Build object */ },
  "ai_analysis": { /* Analysis */ },
  "similar_builds": []
}
```

### GET `/builds`
List all builds.

**Query Parameters:**
- `profession`: Filter by profession
- `game_mode`: Filter by game mode
- `role`: Filter by role
- `limit`: Max results (default: 20)

### GET `/builds/{build_id}`
Get a specific build.

## Team Endpoints

### POST `/teams/optimize`
Optimize a team composition.

**Request:**
```json
{
  "game_mode": "zerg",
  "team_size": 25,
  "required_roles": {
    "tank": 2,
    "support": 5,
    "dps": 18
  },
  "constraints": "High boon uptime"
}
```

**Response:**
```json
{
  "team": { /* Team object */ },
  "ai_recommendations": { /* Recommendations */ },
  "alternative_compositions": []
}
```

### GET `/teams`
List all team compositions.

### GET `/teams/{team_id}`
Get a specific team.

## Learning Endpoints

### GET `/learning/stats`
Get learning system statistics.

**Response:**
```json
{
  "total_datapoints": 150,
  "validated_datapoints": 120,
  "average_quality_score": 7.5,
  "high_quality_count": 80,
  "medium_quality_count": 30,
  "low_quality_count": 10,
  "datapoints_by_source": {
    "ai_generated": 100,
    "parsed_gw2skill": 30,
    "community_scrape": 20
  }
}
```

### POST `/learning/pipeline/run`
Manually trigger the learning pipeline (runs in background).

### GET `/learning/config/finetuning`
Get fine-tuning configuration.

### POST `/learning/config/finetuning`
Update fine-tuning configuration.

### GET `/learning/config/storage`
Get storage configuration.

### POST `/learning/config/storage`
Update storage configuration.

### POST `/learning/cleanup`
Manually trigger storage cleanup.

## Error Responses

All endpoints may return error responses:

```json
{
  "detail": "Error message"
}
```

**Status Codes:**
- 200: Success
- 400: Bad Request
- 404: Not Found
- 500: Internal Server Error
- 503: Service Unavailable
