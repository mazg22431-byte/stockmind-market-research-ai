
import os
def get_secret(name,default=""):
    # Prefer Vault Agent injected env/file. Never log returned secret.
    env=os.getenv(name)
    if env:return env
    vault_file=os.getenv("VAULT_FILE_"+name)
    if vault_file and os.path.exists(vault_file):
        return open(vault_file,encoding="utf-8").read().strip()
    return default
