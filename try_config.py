import yaml

# Load config.yaml
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Access values
print(config)                 # Print the entire config
print(config.get("postgres_database")) # Example: access a key called "database"
