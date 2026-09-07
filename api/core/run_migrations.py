from api.core.migrations import run_compatible_migrations


if __name__ == "__main__":
    run_compatible_migrations()
    print("Database migrations completed successfully.")