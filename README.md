# Install

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

# Configure

```bash
export SECRET_KEY="change-me-in-production"
# Optional, defaults to sqlite:///app.db
# export DATABASE_URL="sqlite:///app.db"
```

# Database setup

```bash
flask --app app db upgrade
```

# Run (development)

```bash
flask --app app run --host 0.0.0.0 --port 8000
```

# Run (production)

```bash
./run.sh
```
