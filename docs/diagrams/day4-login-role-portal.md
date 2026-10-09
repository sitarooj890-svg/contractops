# Day 4 - Login, Role and Portal

Week 1 flow: landing page to login, FastAPI issuing a JWT, then routing each
user to the portal for their role (with the unauthenticated and 403 branches).

````mermaid
flowchart TD
    A["User opens the web app landing page"] --> B["Clicks Log In in the top bar"]
    B --> C["Login form submits email and password"]
    C --> D["POST /auth/login to FastAPI"]
    D --> E{"FastAPI checks the bcrypt password hash"}
    E -->|"Invalid password"| F["401 Invalid email or password"]
    F --> C
    E -->|"Valid password"| G["FastAPI issues a JWT valid for 60 minutes"]
    G --> H["Browser saves the token in localStorage"]
    H --> I["Redirect to /dashboard with Full Name, Email and Role"]
    J["User opens /dashboard unauthenticated"] --> K["ProtectedRoute redirects to /login"]
    K --> C
    I --> L{"Role check decision: Analyst, Approver or Admin"}
    L -->|"Analyst"| M["Navigate to /analyst Analyst Portal"]
    L -->|"Approver"| N["Navigate to /approver Approver Portal"]
    L -->|"Admin"| O["Navigate to /admin Admin Users page"]
    M --> P["Portal page renders"]
    N --> P
    O --> P
    Q["User opens a portal route outside their role"] --> R["RequireRole rejects the route"]
    R --> S["403 Permission Denied page"]
    S --> I
````
