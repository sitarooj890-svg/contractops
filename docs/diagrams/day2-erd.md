# Day 2 — ERD (core schema)

10 tables. PK/FK shown in diagram. Named UNIQUE + CHECK listed as comments.

```mermaid
erDiagram
    users {
        int id PK
        string email "uq_users_email"
        string password_hash
        string full_name
        timestamptz created_at
    }
    %% uq_users_email UNIQUE(email)

    organizations {
        int id PK
        string name "uq_organizations_name"
        timestamptz created_at
    }
    %% uq_organizations_name UNIQUE(name)

    memberships {
        int id PK
        int user_id FK
        int organization_id FK
        string role "ck_memberships_role_valid"
        timestamptz created_at
    }
    %% ck_memberships_role_valid CHECK(role IN analyst,approver,admin)
    %% uq_memberships_user_organization UNIQUE(user_id, organization_id)

    contracts {
        int id PK
        int organization_id FK
        string title
        string source_id "nullable, uq_contracts_organization_source_id"
        int created_by FK
        timestamptz created_at
    }
    %% uq_contracts_organization_source_id UNIQUE(organization_id, source_id)

    parties {
        int id PK
        string name
        timestamptz created_at
    }

    contract_parties {
        int contract_id PK_FK
        int party_id PK_FK
    }
    %% PK(contract_id, party_id)

    document_versions {
        int id PK
        int contract_id FK
        int version_number "ck_document_versions_version_number_positive"
        string file_name
        string status
        timestamptz created_at
    }
    %% uq_document_versions_contract_version UNIQUE(contract_id, version_number)
    %% ck_document_versions_version_number_positive CHECK(version_number >= 1)

    obligations {
        int id PK
        int contract_id FK
        int document_version_id FK_nullable
        text description
        date due_date_nullable
        string status "ck_obligations_status_valid"
        int created_by FK
        timestamptz created_at
        timestamptz updated_at
    }
    %% ck_obligations_status_valid CHECK(status IN draft,approved,rejected)

    approvals {
        int id PK
        int obligation_id FK
        int approver_id FK
        string action "ck_approvals_action_valid"
        text comment_nullable
        timestamptz created_at
    }
    %% ck_approvals_action_valid CHECK(action IN confirm,correct,reject)

    audit_logs {
        int id PK
        int user_id FK_nullable
        string action
        string entity_type
        int entity_id_nullable
        timestamptz created_at
    }

    users ||--o{ memberships : "user_id"
    organizations ||--o{ memberships : "organization_id"
    organizations ||--o{ contracts : "organization_id"
    users ||--o{ contracts : "created_by"
    contracts ||--o{ contract_parties : "contract_id"
    parties ||--o{ contract_parties : "party_id"
    contracts ||--o{ document_versions : "contract_id"
    contracts ||--o{ obligations : "contract_id"
    document_versions |o--o{ obligations : "document_version_id?"
    users ||--o{ obligations : "created_by"
    obligations ||--o{ approvals : "obligation_id"
    users ||--o{ approvals : "approver_id"
    users |o--o{ audit_logs : "user_id?"
```
