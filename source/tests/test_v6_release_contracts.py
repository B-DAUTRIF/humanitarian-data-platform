from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "source"


class V6ReleaseContractTest(unittest.TestCase):
    def test_windows_builds_target_the_development_version(self) -> None:
        installer = (SOURCE / "src" / "installer.c").read_text(encoding="utf-8")
        resources = (SOURCE / "src" / "installer.rc").read_text(encoding="utf-8")
        manifest = (SOURCE / "src" / "installer.manifest").read_text(encoding="utf-8")
        powershell = (SOURCE / "build-windows.ps1").read_text(encoding="utf-8")
        zig = (SOURCE / "build.sh").read_text(encoding="utf-8")
        name = "HumanitarianDataPlatform_Setup_Native_GUI_v6.0.0-dev.exe"
        self.assertIn('#define APP_VERSION L"6.0.0-dev"', installer)
        self.assertIn("FILEVERSION 6,0,0,0", resources)
        self.assertIn('VALUE "ProductVersion", "6.0.0-dev"', resources)
        self.assertIn('assemblyIdentity version="6.0.0.0"', manifest)
        self.assertIn(name, powershell)
        self.assertIn(name, zig)
        self.assertIn("ole32.lib", powershell)
        self.assertIn("uuid.lib", powershell)
        self.assertIn("-lole32", zig)
        self.assertIn("-luuid", zig)

    def test_recreation_prompt_and_evaluation_are_canonical(self) -> None:
        prompt = ROOT / "HDP_Prompt_recreation_global_v6.0.0.txt"
        report = ROOT / "docs" / "RAPPORT_CONFORMITE_ET_EVALUATION_V6.md"
        self.assertTrue(prompt.is_file())
        self.assertTrue(report.is_file())
        prompt_text = prompt.read_text(encoding="utf-8")
        for marker in (
            "RÈGLES ET ALERTES",
            "CONNECTEURS, PARAMÈTRES ET CATALOGUE",
            "RSS ET VEILLE SANITAIRE MONDIALE",
            "SAUVEGARDES ET CHRONOLOGIES",
            "INTERDICTIONS DE PRÉSENTATION",
        ):
            self.assertIn(marker, prompt_text)
        self.assertIn("Toutes les demandes", report.read_text(encoding="utf-8"))

    def test_packaging_contract_requires_and_validates_a_real_pe(self) -> None:
        script_path = ROOT / "tools" / "package_v6_release.py"
        spec = importlib.util.spec_from_file_location("package_v6_release", script_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.VERSION, "6.0.0-dev")
        self.assertEqual(
            module.INSTALLER_NAME,
            "HumanitarianDataPlatform_Setup_Native_GUI_v6.0.0-dev.exe",
        )
        files = {path.relative_to(ROOT).as_posix() for path in module.iter_source_files()}
        self.assertIn("source/src/installer.c", files)
        self.assertIn("source/payload/.env.example", files)
        self.assertNotIn("source/src/payload_generated.h", files)
        self.assertNotIn("source/HumanitarianDataPlatform_Setup_Native_GUI_v3.0.0.exe", files)
        self.assertNotIn("source/HumanitarianDataPlatform_Setup_Native_GUI_v3.0.0.exe.sha256", files)
        self.assertFalse(any("__pycache__" in path for path in files))


if __name__ == "__main__":
    unittest.main()
