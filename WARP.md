# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

SmartShopper AI is an intelligent shopping assistant powered by artificial intelligence. The application leverages AI to analyze products, compare prices, and provide personalized recommendations.

## Technology Stack

- **Language**: Python (primary)
- **Databases**: Redis (caching), Elasticsearch (search and analytics)
- **Containerization**: Docker Compose for local development
- **Build System**: Make

## Development Commands

### Infrastructure
```bash
# Start all services (Redis, Elasticsearch, Kibana)
make up

# Stop all services
make down

# View service logs
make logs

# Connect to Redis CLI
make redis-cli

# Check Elasticsearch health
make es-status

# Clean up everything (including volumes)
make clean

# Restart all services
make restart
```

### Service Endpoints
- **Redis**: localhost:6379
- **Elasticsearch**: localhost:9200
- **Kibana**: localhost:5601

## Project Structure

```
smartshopper-ai/
├── src/          # Source code (currently empty)
├── tests/        # Test files (currently empty)
├── docs/         # Documentation (currently empty)
├── docker-compose.yml  # Local development services
├── Makefile      # Development commands
├── README.md     # Project documentation
└── .gitignore    # Comprehensive ignore file for Python/Node.js
```

## Architecture Notes

This is an early-stage project with basic infrastructure in place. The codebase is structured to support:

1. **Multi-language support**: .gitignore includes patterns for both Python and Node.js, suggesting potential full-stack development
2. **Microservices-ready**: Docker Compose setup allows for easy service scaling
3. **Search and caching**: Elasticsearch for product search/analytics, Redis for caching and session management

## Development Workflow

1. **Start infrastructure**: Run `make up` to start Redis and Elasticsearch
2. **Verify services**: Use `make es-status` to ensure Elasticsearch is healthy
3. **Development**: Add code to `src/` directory
4. **Testing**: Add tests to `tests/` directory
5. **Documentation**: Update `docs/` as needed

## Key Considerations

- The project uses persistent Docker volumes for data storage
- Elasticsearch runs in single-node mode with security disabled (development only)
- Redis is configured with append-only persistence
- The infrastructure setup prioritizes ease of development over production readiness