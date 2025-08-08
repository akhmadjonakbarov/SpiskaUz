import os

# APPS_DIR = r"C:\Users\Akhmad\Desktop\djangoProjects\spiska_uz\apps"

def delete_migration_files(apps_dir):
    deleted_files = []
    for app_name in os.listdir(apps_dir):
        app_path = os.path.join(apps_dir, app_name)
        if not os.path.isdir(app_path):
            continue

        migrations_path = os.path.join(app_path, 'migrations')
        if not os.path.exists(migrations_path):
            continue

        for file_name in os.listdir(migrations_path):
            if file_name != '__init__.py' and file_name.endswith(('.py', '.pyc')):
                file_path = os.path.join(migrations_path, file_name)
                try:
                    os.remove(file_path)
                    deleted_files.append(file_path)
                except Exception as e:
                    print(f"⚠️ Could not delete {file_path}: {e}")

    if deleted_files:
        print("\n ✅ Deleted migration files:")
        for f in deleted_files:
            print(f" ✅ {f}")
    else:
        print("ℹ️ No migration files found to delete.")

if __name__ == "__main__":
    delete_migration_files('apps')
