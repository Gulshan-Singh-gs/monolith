"""
Instant Cookie Session Vault for Sovereign On-Premise Agentic AI Workbench (SIH PSC26117)
Enables instant browser login without passwords or OTP delays by rehydrating
pre-saved authenticated session states and cookies directly into Playwright contexts.

Security: All stored session cookies and sensitive metadata are encrypted at rest
using authenticated symmetric encryption (Fernet / AES-128-CBC + HMAC-SHA256).
The encryption key is stored securely in an isolated key file (.vault_key) with restricted access.
No hardcoded or fabricated authentication tokens are shipped in production paths.
"""
import os
import json
import time
import base64
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from cryptography.fernet import Fernet

logger = logging.getLogger("CookieVault")

VAULT_DIR = Path(__file__).resolve().parent / "session_vault"
VAULT_FILE = VAULT_DIR / "portal_sessions.enc"
KEY_FILE = VAULT_DIR / ".vault_key"


class CookieVault:
    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or VAULT_DIR
        self.storage_file = self.storage_dir / "portal_sessions.enc"
        self.legacy_plaintext_file = self.storage_dir / "portal_sessions.json"
        self.key_file = self.storage_dir / ".vault_key"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._cipher = self._init_cipher()
        self._migrate_legacy_if_present()

    def _init_cipher(self) -> Fernet:
        """Loads or creates the Fernet encryption key for the vault."""
        key = None
        # Check environment variable first (for external KMS / container secret injection)
        env_key = os.environ.get("SOVEREIGN_VAULT_KEY")
        if env_key:
            try:
                key = env_key.encode("utf-8")
                return Fernet(key)
            except Exception as e:
                logger.warning(f"Invalid SOVEREIGN_VAULT_KEY in environment: {e}")

        if self.key_file.exists():
            try:
                key = self.key_file.read_bytes().strip()
                return Fernet(key)
            except Exception as e:
                logger.warning(f"Error reading existing vault key: {e}. Generating fresh key.")

        # Generate a high-entropy 256-bit key (base64 encoded as 32 url-safe base64-encoded bytes)
        key = Fernet.generate_key()
        try:
            self.key_file.write_bytes(key)
            # Set restrictive file permissions on POSIX systems if supported
            try:
                os.chmod(self.key_file, 0o600)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Could not persist vault key to disk: {e}")
        return Fernet(key)

    def _migrate_legacy_if_present(self):
        """Migrates any existing unencrypted portal_sessions.json to encrypted storage and purges the plaintext file."""
        if self.legacy_plaintext_file.exists():
            try:
                with open(self.legacy_plaintext_file, "r", encoding="utf-8") as f:
                    legacy_data = json.load(f)
                if isinstance(legacy_data, dict):
                    # Filter out any hardcoded demo tokens during migration
                    clean_data = {}
                    for domain, item in legacy_data.items():
                        cookies = item.get("cookies", [])
                        sanitized_cookies = []
                        for c in cookies:
                            # Strip out known mock/demo values
                            val = c.get("value", "")
                            if "gem_auth_tok_" in val or "sovereign_verified_officer" in val:
                                continue
                            sanitized_cookies.append(c)
                        if sanitized_cookies or not cookies:
                            item["cookies"] = sanitized_cookies
                            clean_data[domain] = item
                    self._save_store(clean_data)
                # Securely wipe plaintext legacy file
                self.legacy_plaintext_file.unlink(missing_ok=True)
                logger.info("Migrated legacy plaintext cookie vault to encrypted vault.")
            except Exception as e:
                logger.warning(f"Error during legacy vault migration: {e}")

    def _read_store(self) -> Dict[str, Any]:
        """Decrypts and returns the vault store."""
        if not self.storage_file.exists():
            return {}
        try:
            enc_bytes = self.storage_file.read_bytes()
            if not enc_bytes:
                return {}
            dec_bytes = self._cipher.decrypt(enc_bytes)
            return json.loads(dec_bytes.decode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to decrypt cookie vault store (possible corruption or key mismatch): {e}")
            return {}

    def _save_store(self, data: Dict[str, Any]):
        """Encrypts and atomically writes the vault store to disk."""
        try:
            raw_json = json.dumps(data, indent=2).encode("utf-8")
            enc_bytes = self._cipher.encrypt(raw_json)
            # Atomic write via temporary file
            temp_file = self.storage_file.with_suffix(".tmp")
            temp_file.write_bytes(enc_bytes)
            try:
                os.chmod(temp_file, 0o600)
            except Exception:
                pass
            temp_file.replace(self.storage_file)
        except Exception as e:
            logger.error(f"Failed to persist encrypted cookie vault store: {e}")

    def list_sessions(self) -> List[Dict[str, Any]]:
        """Lists active portal sessions metadata without exposing raw cookie secrets."""
        store = self._read_store()
        result = []
        for domain, details in store.items():
            result.append({
                "domain": domain,
                "portal_name": details.get("portal_name", domain),
                "portal_url": details.get("portal_url", ""),
                "user_role": details.get("user_role", "Government Officer"),
                "organization": details.get("organization", "Central Government"),
                "status": details.get("status", "Active"),
                "saved_at": details.get("saved_at", ""),
                "cookie_count": len(details.get("cookies", [])),
            })
        return result

    def get_cookies_for_domain(self, domain_or_url: str) -> List[Dict[str, Any]]:
        """Retrieves decrypted cookies for browser injection upon authorized invocation."""
        store = self._read_store()
        clean = domain_or_url.replace("https://", "").replace("http://", "").split("/")[0]
        if clean in store:
            return store[clean].get("cookies", [])
        for domain, details in store.items():
            if domain in clean or clean in domain:
                return details.get("cookies", [])
        return []

    async def inject_into_context(self, context, url: str) -> bool:
        """Injects preserved cookies directly into Playwright browser context."""
        cookies = self.get_cookies_for_domain(url)
        if not cookies:
            return False
        try:
            await context.add_cookies(cookies)
            return True
        except Exception as e:
            logger.warning(f"Error injecting cookies into browser context: {e}")
            return False

    def get_session(self, domain: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific portal session by domain."""
        store = self._read_store()
        return store.get(domain)

    def delete_session(self, domain: str) -> bool:
        """Deletes a portal session from the vault."""
        store = self._read_store()
        if domain in store:
            del store[domain]
            self._save_store(store)
            return True
        return False

    def save_session(
        self,
        domain: str,
        portal_name: str,
        cookies: List[Dict[str, Any]],
        role: str,
        org: str,
        portal_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Encrypts and saves authenticated session cookies for a portal."""
        store = self._read_store()
        clean_domain = domain.strip().replace("https://", "").replace("http://", "").split("/")[0]
        url = portal_url or f"https://{clean_domain}"
        store[clean_domain] = {
            "portal_name": portal_name or clean_domain,
            "portal_url": url,
            "user_role": role or "Government Officer",
            "organization": org or "Central Government",
            "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Authenticated (Session Valid)",
            "cookies": cookies,
        }
        self._save_store(store)
        return store[clean_domain]
