# Chatbot

This is a basic Flask project that exposes several REST API endpoints for e-commerce features, such as to retrieve order details by ID.

For a more detailed description of the features in this project, please see [the user stories](./user-stories.md)

## Endpoint

- **GET** `/orders/<id>`
  Returns the details of the order with the specified ID.

## Project Structure

```
chatbot/
├── app/
│   ├── __init__.py  # Initializes the Flask app and registers blueprints
│   └── routes.py    # Contains the /orders/ endpoint
└── run.py # Entry point to run the Flask application
README.md # Project documentation
```

## Running the Project

1. Create a virtual environment and activate it (on Windows):
   ```bash
   python -m venv venv
   Set-ExecutionPolicy Unrestricted -Scope Process
   .\\venv\\Scripts\\activate
1. Create a virtual environment and activate it (on Mac):
   ```bash
   python -m venv venv
   source venv/bin/activate
2. Install flask:
   ```bash
   pip install Flask
3. Run the application:
   ```bash
   python .\\chatbot\\run.py
4. Access the API at: http://127.0.0.1:5000/orders/1

### Example Response
```json
{
  "order_id": 1,
  "details": {
    "item": "Laptop",
    "quantity": 1
  }
}
```

## Authentication & Session Management

Register a new user by running the following command in PowerShell:
```bash
   Invoke-RestMethod -Uri http://127.0.0.1:5000/users/register `  -Method POST `  -Body (@{username="alice"; password="password123"} | ConvertTo-Json) `  -ContentType "application/json"
```

Login by running the following command in PowerShell:
```bash
   Invoke-RestMethod -Uri http://127.0.0.1:5000/users/login `  -Method POST `  -Body (@{username="alice"; password="password123"} | ConvertTo-Json) `  -ContentType "application/json"
```
