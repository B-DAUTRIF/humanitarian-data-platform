from __future__ import annotations

import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = SOURCE_ROOT / "src" / "installer.c"


class V6InstallerReliabilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = INSTALLER.read_text(encoding="utf-8")

    def test_captured_processes_are_polled_instead_of_read_indefinitely(self) -> None:
        self.assertIn("run_process_capture_timeout", self.source)
        self.assertIn("PeekNamedPipe", self.source)
        self.assertNotIn("WaitForSingleObject(process.hProcess, INFINITE)", self.source)

    def test_long_installer_operations_have_explicit_limits(self) -> None:
        for constant in (
            "WINGET_TIMEOUT_MS",
            "COMPOSE_PULL_TIMEOUT_MS",
            "COMPOSE_BUILD_TIMEOUT_MS",
            "COMPOSE_UP_TIMEOUT_MS",
            "COMPOSE_LOGS_TIMEOUT_MS",
        ):
            self.assertIn(constant, self.source)
            self.assertIn(f", {constant})", self.source)
        self.assertIn("ERROR_TIMEOUT", self.source)

    def test_cancel_stops_the_process_tree_and_preserves_data(self) -> None:
        for marker in (
            "ID_CANCEL",
            "g_cancel_requested",
            "JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE",
            "TerminateJobObject",
            "ERROR_CANCELLED",
            "Annulation demandée",
            "données et volumes existants sont conservés",
        ):
            self.assertIn(marker, self.source)
        lowered = self.source.casefold()
        self.assertNotIn("down -v", lowered)
        self.assertNotIn("volume rm", lowered)

    def test_silent_commands_report_periodic_activity(self) -> None:
        self.assertIn("next_heartbeat", self.source)
        self.assertIn("Commande toujours active", self.source)
        self.assertIn("30ULL * 1000ULL", self.source)

    def test_docker_and_web_waits_observe_cancellation(self) -> None:
        self.assertGreaterEqual(self.source.count("if (cancel_requested())"), 3)
        self.assertIn("6ULL * 60ULL * 1000ULL", self.source)
        self.assertIn("for (int attempt = 0; attempt < 100; attempt++)", self.source)

    def test_successful_installation_creates_a_native_desktop_shortcut(self) -> None:
        build = (SOURCE_ROOT / "build-windows.ps1").read_text(encoding="utf-8")
        for marker in (
            "create_desktop_shortcut",
            "CSIDL_DESKTOPDIRECTORY",
            "CLSID_ShellLink",
            "IPersistFile_Save",
            "Humanitarian Data Platform.lnk",
            "start-hdp-with-r.cmd",
            "start-hdp.cmd",
        ):
            self.assertIn(marker, self.source)
        self.assertIn("ole32.lib", build)
        self.assertIn("uuid.lib", build)

    def test_uninstall_requires_an_installer_marker_and_exact_payload_paths(self) -> None:
        for marker in (
            "INSTALLATION_MARKER_NAME",
            "INSTALLATION_MARKER_CONTENT",
            "write_installation_marker",
            "installation_marker_is_valid",
            "installation_path_is_safe",
            "payload_relative_path_is_safe",
            "remove_managed_payload",
            "g_payload_file_count",
        ):
            self.assertIn(marker, self.source)
        self.assertNotIn("RemoveDirectoryW", self.source)
        self.assertLess(
            self.source.index("remove_managed_payload(options->install_dir"),
            self.source.index("DeleteFileW(marker_path)"),
        )

    def test_uninstall_stops_compose_without_removing_data_or_third_party_tools(self) -> None:
        for marker in (
            "ID_UNINSTALL",
            "uninstall_thread",
            "begin_uninstall",
            "down --remove-orphans",
            ".env, data, sauvegardes, journaux et volumes PostgreSQL sont conservés",
            "Docker Desktop, Git et Visual Studio Code restent installés",
        ):
            self.assertIn(marker, self.source)
        lowered = self.source.casefold()
        self.assertNotIn("down -v", lowered)
        self.assertNotIn("volume rm", lowered)
        self.assertNotIn("winget uninstall", lowered)

    def test_uninstall_removes_only_the_shortcut_targeting_this_installation(self) -> None:
        for marker in (
            "remove_managed_desktop_shortcut",
            "IPersistFile_Load",
            "IShellLinkW_GetPath",
            "start-hdp.cmd",
            "start-hdp-with-r.cmd",
            "DeleteFileW(shortcut)",
            "ne cible pas cette installation ; il est conservé",
        ):
            self.assertIn(marker, self.source)

    def test_installer_declares_the_v6_development_version(self) -> None:
        resources = (SOURCE_ROOT / "src" / "installer.rc").read_text(encoding="utf-8")
        manifest = (SOURCE_ROOT / "src" / "installer.manifest").read_text(encoding="utf-8")
        self.assertIn('#define APP_VERSION L"6.0.0-dev"', self.source)
        self.assertIn(".env.backup-before-v6.0.0", self.source)
        self.assertIn("FILEVERSION 6,0,0,0", resources)
        self.assertIn('assemblyIdentity version="6.0.0.0"', manifest)


if __name__ == "__main__":
    unittest.main()
