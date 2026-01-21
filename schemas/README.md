# Schema Configuration System

## Overview

This system uses declarative YAML files to define database schemas and JOIN paths, making it easy to onboard new databases and improve LLM query generation accuracy.

## Directory Structure

```
schemas/
├── template.yaml          # Template for new databases
├── tpch.yaml             # TPC-H configuration
├── ai_insights.yaml      # AI Insights configuration
└── your_db.yaml          # Add your databases here
```

## How It Works

1. **Load Config**: System loads `schemas/{database_name}.yaml`
2. **Format for LLM**: Converts YAML to structured text prompt
3. **Fallback**: If no config exists, auto-generates from MySQL INFORMATION_SCHEMA

## Adding a New Database

### Step 1: Copy Template

```bash
cp schemas/template.yaml schemas/my_database.yaml
```

### Step 2: Define Tables

```yaml
tables:
  users:
    description: "System users"
    primary_key: id
    important_columns:
      - name: "User full name"
      - email: "Email address"
      - role: "User role (admin/user)"
```

### Step 3: Define Foreign Keys

```yaml
tables:
  orders:
    primary_key: id
    foreign_keys:
      - column: user_id
        references: users.id
```

### Step 4: Define JOIN Paths

This is the **most important** section for complex queries:

```yaml
join_paths:
  orders_to_user:
    description: "Get user info for an order"
    path:
      - from: orders
        to: users
        on: "orders.user_id = users.id"
    example: "Show orders with customer names"
```

For multi-hop JOINs:

```yaml
join_paths:
  lineitems_to_customer:
    description: "Get customer for a line item"
    path:
      - from: lineitems
        to: orders
        on: "lineitems.order_id = orders.id"
      - from: orders
        to: users
        on: "orders.user_id = users.id"
    example: "Show line items by customer"
```

### Step 5: (Optional) Add Query Patterns

```yaml
query_patterns:
  top_users:
    template: "SELECT u.name, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.name ORDER BY COUNT DESC LIMIT 10"
    description: "Top users by order count"
```

## Benefits

✅ **Explicit JOIN Paths**: LLM knows exactly how to join tables
✅ **Business Context**: Add descriptions that help LLM understand data
✅ **Easy Onboarding**: Non-technical users can add databases using YAML
✅ **Version Control**: Schema configs are in Git
✅ **Validation**: System validates config against actual database
✅ **Fallback**: Works even without config (auto-generates from MySQL)

## Best Practices

1. **Start Simple**: Define tables and basic JOINs first
2. **Add Complex Paths**: Define multi-hop JOINs explicitly
3. **Use Descriptions**: Help LLM understand business context
4. **Test Queries**: Add common patterns as examples
5. **Keep Updated**: Update config when schema changes

## Example: TPC-H

See `schemas/tpch.yaml` for a complete example with:
- 5 tables defined
- All foreign keys mapped
- 3 common JOIN paths
- Query pattern examples

## Troubleshooting

**Q: My database isn't using the config**
A: Check filename matches database name exactly (e.g., `tpch.yaml` for database `tpch`)

**Q: Joins still incorrect**
A: Add explicit `join_paths` section with the correct path

**Q: LLM using wrong columns**
A: Add column descriptions in `important_columns` to clarify purpose

## Future Enhancements

- Validation tool to check config against actual DB
- Web UI for config management
- Auto-generation of initial config from schema introspection
- Support for JSON format (in addition to YAML)
