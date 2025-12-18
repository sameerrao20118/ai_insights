# Documentation Directory

Comprehensive documentation for the AI Insights platform.

## Architecture & Design

### [ARCHITECTURE.md](ARCHITECTURE.md)
Complete architecture documentation including:
- LLM selection strategy
- Platform recommendation engine
- System design patterns
- Component interactions

**Key Topics:**
- Multi-provider LLM support (Ollama, Azure OpenAI, Gemini)
- Vector database architecture
- Authentication and security
- Scalability considerations

---

### [ENTERPRISE_SETUP.md](ENTERPRISE_SETUP.md)
Enterprise deployment guide covering:
- Complete solution documentation
- Fixes and enhancements
- Enterprise components
- Testing scripts
- Common issues and resolutions

**Sections:**
- Authentication (`auth.py`)
- LLM Client (`llm/lm_interface.py`)
- Embeddings Service
- Testing protocols
- Deployment checklist

---

### [CHANGELOG_ENTERPRISE.md](CHANGELOG_ENTERPRISE.md)
Version history and changes for enterprise features:
- Authentication improvements
- LLM configuration updates
- Bug fixes
- Feature additions

---

## Additional Documentation

For complete setup instructions, see the main [README.md](../README.md) in the project root.

## Quick Navigation

| Topic | Document | Description |
|-------|----------|-------------|
| System Architecture | ARCHITECTURE.md | Overall system design |
| Enterprise Setup | ENTERPRISE_SETUP.md | Deployment guide |
| Change History | CHANGELOG_ENTERPRISE.md | Version history |
| Setup Guide | ../README.md | Installation & configuration |
| API Reference | ../AI_Insights_API.postman_collection.json | API endpoints |

## Document Hierarchy

```
docs/
├── ARCHITECTURE.md          # System design (read first for understanding)
├── ENTERPRISE_SETUP.md      # Deployment guide (read for setup)
└── CHANGELOG_ENTERPRISE.md  # Version history (reference as needed)

../
├── README.md                # Main setup guide (start here)
└── AI_Insights_API.postman_collection.json  # API documentation
```

## Recommended Reading Order

### For New Users
1. [README.md](../README.md) - Installation and basic setup
2. [ARCHITECTURE.md](ARCHITECTURE.md) - Understand the system
3. [ENTERPRISE_SETUP.md](ENTERPRISE_SETUP.md) - Enterprise deployment

### For Developers
1. [ARCHITECTURE.md](ARCHITECTURE.md) - System design
2. [README.md](../README.md) - Local development setup
3. API collection - Testing and integration

### For Operations
1. [ENTERPRISE_SETUP.md](ENTERPRISE_SETUP.md) - Deployment procedures
2. [CHANGELOG_ENTERPRISE.md](CHANGELOG_ENTERPRISE.md) - Version tracking
3. [README.md](../README.md) - Troubleshooting

## Contributing

When adding new documentation:
1. Place architecture/design docs in this directory
2. Keep the main README.md for setup instructions
3. Update this index when adding new documents
4. Use clear headings and cross-references
