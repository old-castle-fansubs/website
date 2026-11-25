export DJANGO_SETTINGS_MODULE := "oc_website.settings"
export DEBUG := "1"
export SECRET_KEY := "dev"
export HOST_SITE := "http://localhost:8000"
export ANIDEX_API_KEY := "dev"
export ANIDEX_GROUP_ID := "0"
export NYAA_SI_USER := "dev"
export NYAA_SI_PASS := "dev"
export ANIDB_CLIENT := "dev"
export ANIDB_CLIENTVER := "1"

# Run manage.py
manage *args:
    cd app && uv run python manage.py {{args}}

# Migrate the local database (app/db.sqlite3) and serve on localhost:8000
dev port="8000": (manage "migrate") (manage "runserver" port)

# Run the tests
test *args:
    uv run pytest {{args}}
