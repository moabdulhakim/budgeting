# Budgeting

## How to Run the Code

**1. Create and activate a virtual environment:**

* **Windows:**
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    ```
* **Linux / macOS:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Apply database migrations:**
Navigate to the project directory (where manage.py is located) and run:

```bash
python manage.py migrate
```

**4. Start the server:**

```bash
python manage.py runserver
```
