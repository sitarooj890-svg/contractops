# Day 2 - ERD (core schema)

10 tables. PK = primary key, FK = foreign key, UK = unique.

````mermaid
erDiagram
    users {
        int id PK
        string email UK
        string password_hash
        string full_name
        timestamp created_at
    }
    organizations {
        int id PK
        string name UK
        timestamp created_at
    }
    memberships {
        int id PK
        int user_id FK
        int organization_id FK
        string role
        timestamp created_at
    }
    contracts {
        int id PK
        int organization_id FK
        string title
        string source_id
        int created_by FK
        timestamp created_at
    }
    parties {
        int id PK
        string name
        timestamp created_at
    }
    contract_parties {
        int contract_id PK, FK
        int party_id PK, FK
    }
    document_versions {
        int id PK
        int contract_id FK
        int version_number
        string file_name
        string status
        timestamp created_at
    }
    obligations {
        int id PK
        int contract_id FK
        int document_version_id FK
        text description
        date due_date
        string status
        int created_by FK
        timestamp created_at
        timestamp updated_at
    }
    approvals {
        int id PK
        int obligation_id FK
        int approver_id FK
        string action
        text comment
        timestamp created_at
    }
    audit_logs {
        int id PK
        int user_id FK
        string action
        string entity_type
        int entity_id
        timestamp created_at
    }

    users ||--o{ memberships : has
    organizations ||--o{ memberships : has
    organizations ||--o{ contracts : owns
    users ||--o{ contracts : creates
    contracts ||--o{ contract_parties : involves
    parties ||--o{ contract_parties : appears_in
    contracts ||--o{ document_versions : has
    contracts ||--o{ obligations : has
    document_versions |o--o{ obligations : cited_by
    obligations ||--o{ approvals : reviewed_in
    users ||--o{ approvals : decides
    users ||--o{ obligations : drafts
    users |o--o{ audit_logs : performs
````

## Constraints

| Table | Constraint | Rule |
|---|---|---|
| users | uq_users_email | One account per email |
| organizations | uq_organizations_name | Organization names are unique |
| memberships | ck_memberships_role_valid | role is analyst, approver or admin |
| memberships | uq_memberships_user_organization | One membership per user per organization |
| contracts | uq_contracts_organization_source_id | A source ID is unique inside one organization |
| document_versions | uq_document_versions_contract_version | Each version number appears once per contract |
| document_versions | ck_document_versions_version_number_positive | version_number is at least 1 |
| obligations | ck_obligations_status_valid | status is draft, approved or rejected |
| approvals | ck_approvals_action_valid | action is confirm, correct or reject |
