# Day 3 - Login Flow

Login with email and password, then calling a role-protected endpoint.

````mermaid
sequenceDiagram
    participant B as Browser
    participant A as API
    participant D as PostgreSQL

    B->>A: POST auth login with email and password
    A->>D: SELECT user by email
    D-->>A: row with password hash
    A->>A: verify bcrypt hash
    A->>A: create JWT with user id, expires in 60 minutes
    A-->>B: 200 with access token

    B->>A: GET admin users with Bearer token
    A->>A: decode token with JWT secret
    A->>D: read role from memberships table
    D-->>A: role value
    alt role is admin
        A-->>B: 200 with list of users
    else role is analyst
        A-->>B: 403 forbidden for this role
    end
````
