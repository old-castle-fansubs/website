export DJANGO_SETTINGS_MODULE := "oc_website.settings"
export DEBUG := "1"
export SECRET_KEY := "dev"

# Run manage.py
manage *args:
    cd app && uv run python manage.py {{args}}

# Migrate the local database (app/db.sqlite3) and serve on localhost:8000
dev port="8000": (manage "migrate") (manage "runserver" port)

# Run the tests
test *args:
    uv run pytest {{args}}
