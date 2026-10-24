"""
Headless CI Test Suite for NOKAR
Verifies syntax, core imports, configuration validation, and RAG vault logic
without requiring a physical display, microphone, or audio hardware.
"""
import sys
import unittest
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))


class TestHeadlessModules(unittest.TestCase):

    def test_imports_core_modules(self):
        """Verify core backend modules import cleanly."""
        from core.gemini import _LADDERS, FAST, SMART, SEARCH, LIVE_MODELS
        from core.rag_vault import RagVault
        from core.undo import push_undo, undo_last, can_undo
        from core.confirm import TIMEOUT_SECONDS
        
        self.assertIn(FAST, _LADDERS)
        self.assertIn(SMART, _LADDERS)
        self.assertIn(SEARCH, _LADDERS)
        self.assertTrue(len(LIVE_MODELS) > 0)
        self.assertEqual(TIMEOUT_SECONDS, 90.0)
        self.assertFalse(can_undo())

    def test_rag_vault_engine(self):
        """Verify local RAG vault indexing and querying."""
        from core.rag_vault import RagVault
        vault = RagVault()
        
        # Test file indexing with LICENSE
        license_path = ROOT_DIR / "LICENSE"
        chunk_count = vault.index_file(license_path)
        self.assertGreater(chunk_count, 0)
        
        # Test query
        results = vault.query("Muhammad Anas Raheem", top_k=1)
        self.assertTrue(len(results) > 0)
        self.assertIn("Muhammad Anas Raheem", results[0]["snippet"])

    def test_example_configurations(self):
        """Verify template configuration files exist and contain valid JSON."""
        import json
        
        api_keys_example = ROOT_DIR / "config" / "api_keys.example.json"
        self.assertTrue(api_keys_example.exists(), "api_keys.example.json must exist")
        with open(api_keys_example, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertIn("gemini_api_key", data)
            self.assertIn("assistant_name", data)
            self.assertIn("email", data)

        profile_example = ROOT_DIR / "memory" / "profile.example.json"
        self.assertTrue(profile_example.exists(), "profile.example.json must exist")
        with open(profile_example, "r", encoding="utf-8") as f:
            p_data = json.load(f)
            self.assertIn("identity", p_data)

    def test_actions_discovery(self):
        """Verify actions declare valid TOOL metadata."""
        from actions import rag_vault_action, web_search, browser_control
        
        for mod in (rag_vault_action, web_search, browser_control):
            self.assertTrue(hasattr(mod, "TOOL"), f"{mod.__name__} missing TOOL dict")
            tool_dict = getattr(mod, "TOOL")
            self.assertIn("name", tool_dict)
            self.assertIn("description", tool_dict)


if __name__ == "__main__":
    unittest.main()
