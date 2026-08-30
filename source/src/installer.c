#define UNICODE
#define _UNICODE
#define WIN32_LEAN_AND_MEAN
#define COBJMACROS

#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <commctrl.h>
#include <shellapi.h>
#include <shlobj.h>
#include <winhttp.h>
#include <bcrypt.h>
#include <objbase.h>
#include <shobjidl.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include <wctype.h>

#include "payload_generated.h"

#define APP_NAME L"Humanitarian Data Platform"
#define APP_VERSION L"6.0.0"
#define MAIN_CLASS L"HDP_NATIVE_INSTALLER_30"

#define ID_PATH 1001
#define ID_RELIEFWEB 1002
#define ID_DOCKER 1003
#define ID_GIT 1004
#define ID_VSCODE 1005
#define ID_ANALYZE 1006
#define ID_INSTALL 1007
#define ID_OPEN_FOLDER 1008
#define ID_OPEN_LOG 1009
#define ID_PROGRESS 1010
#define ID_STATUS 1011
#define ID_LOG 1012
#define ID_R_MODULE 1013
#define ID_GITHUB_TOKEN 1014
#define ID_CANCEL 1015
#define ID_UNINSTALL 1016
#define ID_ACTIVITY_TIMER 2001

#define INSTALLATION_MARKER_NAME L".hdp-managed-installation"
#define INSTALLATION_MARKER_CONTENT "HDP_NATIVE_INSTALLER\nHumanitarian Data Platform\n"

#define WINGET_TIMEOUT_MS (30UL * 60UL * 1000UL)
#define COMPOSE_PULL_TIMEOUT_MS (30UL * 60UL * 1000UL)
#define COMPOSE_BUILD_TIMEOUT_MS (45UL * 60UL * 1000UL)
#define COMPOSE_UP_TIMEOUT_MS (10UL * 60UL * 1000UL)
#define COMPOSE_LOGS_TIMEOUT_MS (2UL * 60UL * 1000UL)

#define WM_HDP_LOG (WM_APP + 1)
#define WM_HDP_STATUS (WM_APP + 2)
#define WM_HDP_FINISHED (WM_APP + 3)
#define WM_HDP_ANALYZE (WM_APP + 4)
#define WM_HDP_DOCKER_ACTION (WM_APP + 5)

typedef struct {
    wchar_t install_dir[MAX_PATH * 4];
    wchar_t reliefweb_appname[256];
    wchar_t github_token[512];
    BOOL install_docker;
    BOOL install_git;
    BOOL install_vscode;
    BOOL install_r_module;
    USHORT host_port;
} InstallOptions;

static HINSTANCE g_instance;
static HWND g_main;
static HWND g_path;
static HWND g_reliefweb;
static HWND g_github_token;
static HWND g_docker;
static HWND g_git;
static HWND g_vscode;
static HWND g_r_module;
static HWND g_analyze;
static HWND g_install;
static HWND g_uninstall;
static HWND g_open_folder;
static HWND g_open_log;
static HWND g_cancel;
static HWND g_progress;
static HWND g_status;
static HWND g_log;
static HFONT g_font;
static wchar_t g_log_path[MAX_PATH * 4];
static BOOL g_winget_present;
static BOOL g_docker_present;
static BOOL g_git_present;
static BOOL g_vscode_present;
static BOOL g_installing;
static BOOL g_uninstalling;
static BOOL g_winsock_initialized;
static ULONGLONG g_docker_disk_free_bytes;
static wchar_t g_stage_status[512] = L"Prêt";
static int g_stage_progress;
static ULONGLONG g_stage_started;
static volatile LONG g_cancel_requested;

static BOOL http_is_healthy(USHORT port);
static void update_uninstall_control(void);

static BOOL cancel_requested(void) {
    return InterlockedCompareExchange(&g_cancel_requested, 0, 0) != 0;
}

static wchar_t *heap_wcsdup(const wchar_t *text) {
    size_t count = wcslen(text) + 1;
    wchar_t *copy = HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, count * sizeof(wchar_t));
    if (copy) memcpy(copy, text, count * sizeof(wchar_t));
    return copy;
}

static void post_log(const wchar_t *text) {
    wchar_t *copy = heap_wcsdup(text);
    if (copy) PostMessageW(g_main, WM_HDP_LOG, 0, (LPARAM)copy);
}

static void post_status(const wchar_t *text, int progress) {
    wchar_t *copy = heap_wcsdup(text);
    if (copy) PostMessageW(g_main, WM_HDP_STATUS, (WPARAM)progress, (LPARAM)copy);
}

static void append_log_file(const wchar_t *text) {
    HANDLE file = CreateFileW(g_log_path, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE,
                              NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) return;
    int bytes = WideCharToMultiByte(CP_UTF8, 0, text, -1, NULL, 0, NULL, NULL);
    if (bytes > 1) {
        char *utf8 = HeapAlloc(GetProcessHeap(), 0, (size_t)bytes);
        if (utf8) {
            WideCharToMultiByte(CP_UTF8, 0, text, -1, utf8, bytes, NULL, NULL);
            DWORD written = 0;
            WriteFile(file, utf8, (DWORD)(bytes - 1), &written, NULL);
            HeapFree(GetProcessHeap(), 0, utf8);
        }
    }
    CloseHandle(file);
}

static void append_log_bytes(const char *data, DWORD size) {
    if (!data || !size) return;
    HANDLE file = CreateFileW(g_log_path, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE,
                              NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) return;
    DWORD written = 0;
    WriteFile(file, data, size, &written, NULL);
    CloseHandle(file);
}

static void append_log_control_ex(const wchar_t *text, BOOL persist) {
    int length = GetWindowTextLengthW(g_log);
    SendMessageW(g_log, EM_SETSEL, (WPARAM)length, (LPARAM)length);
    SendMessageW(g_log, EM_REPLACESEL, FALSE, (LPARAM)text);
    SendMessageW(g_log, EM_SCROLLCARET, 0, 0);
    if (persist) append_log_file(text);
}

static void append_log_control(const wchar_t *text) {
    append_log_control_ex(text, TRUE);
}

static BOOL file_exists(const wchar_t *path) {
    DWORD attributes = GetFileAttributesW(path);
    return attributes != INVALID_FILE_ATTRIBUTES && !(attributes & FILE_ATTRIBUTE_DIRECTORY);
}

static BOOL directory_exists(const wchar_t *path) {
    DWORD attributes = GetFileAttributesW(path);
    return attributes != INVALID_FILE_ATTRIBUTES && (attributes & FILE_ATTRIBUTE_DIRECTORY);
}

static BOOL find_program(const wchar_t *name, wchar_t *result, DWORD capacity) {
    DWORD size = SearchPathW(NULL, name, NULL, capacity, result, NULL);
    return size > 0 && size < capacity;
}

static BOOL get_docker_cli(wchar_t *result, DWORD capacity) {
    if (find_program(L"docker.exe", result, capacity)) return TRUE;
    wchar_t program_files[MAX_PATH * 2];
    if (GetEnvironmentVariableW(L"ProgramFiles", program_files, (DWORD)(sizeof(program_files) / sizeof(wchar_t)))) {
        _snwprintf(result, capacity, L"%ls\\Docker\\Docker\\resources\\bin\\docker.exe", program_files);
        if (file_exists(result)) return TRUE;
    }
    wchar_t local_appdata[MAX_PATH * 2];
    if (GetEnvironmentVariableW(L"LOCALAPPDATA", local_appdata, (DWORD)(sizeof(local_appdata) / sizeof(wchar_t)))) {
        _snwprintf(result, capacity, L"%ls\\Programs\\DockerDesktop\\resources\\bin\\docker.exe", local_appdata);
        if (file_exists(result)) return TRUE;
    }
    return FALSE;
}

static BOOL get_docker_desktop(wchar_t *result, DWORD capacity) {
    wchar_t program_files[MAX_PATH * 2];
    if (GetEnvironmentVariableW(L"ProgramFiles", program_files, (DWORD)(sizeof(program_files) / sizeof(wchar_t)))) {
        _snwprintf(result, capacity, L"%ls\\Docker\\Docker\\Docker Desktop.exe", program_files);
        if (file_exists(result)) return TRUE;
    }
    wchar_t local_appdata[MAX_PATH * 2];
    if (GetEnvironmentVariableW(L"LOCALAPPDATA", local_appdata, (DWORD)(sizeof(local_appdata) / sizeof(wchar_t)))) {
        _snwprintf(result, capacity, L"%ls\\Programs\\DockerDesktop\\Docker Desktop.exe", local_appdata);
        if (file_exists(result)) return TRUE;
    }
    return FALSE;
}

static BOOL get_vscode(wchar_t *result, DWORD capacity) {
    if (find_program(L"code.exe", result, capacity)) return TRUE;
    wchar_t base[MAX_PATH * 2];
    if (GetEnvironmentVariableW(L"LOCALAPPDATA", base, (DWORD)(sizeof(base) / sizeof(wchar_t)))) {
        _snwprintf(result, capacity, L"%ls\\Programs\\Microsoft VS Code\\Code.exe", base);
        if (file_exists(result)) return TRUE;
    }
    if (GetEnvironmentVariableW(L"ProgramFiles", base, (DWORD)(sizeof(base) / sizeof(wchar_t)))) {
        _snwprintf(result, capacity, L"%ls\\Microsoft VS Code\\Code.exe", base);
        if (file_exists(result)) return TRUE;
    }
    return FALSE;
}

static void set_dependency_control(HWND control, const wchar_t *name, BOOL present, BOOL winget) {
    wchar_t label[256];
    _snwprintf(label, sizeof(label) / sizeof(wchar_t), L"%ls — %ls", name, present ? L"détecté" : L"absent");
    SetWindowTextW(control, label);
    if (present) SendMessageW(control, BM_SETCHECK, BST_UNCHECKED, 0);
    EnableWindow(control, !g_installing && !present && winget);
}

static void refresh_docker_disk_free_space(void) {
    g_docker_disk_free_bytes = 0;
    wchar_t local_appdata[MAX_PATH * 2];
    if (!GetEnvironmentVariableW(L"LOCALAPPDATA", local_appdata,
                                 (DWORD)(sizeof(local_appdata) / sizeof(wchar_t)))) return;
    ULARGE_INTEGER available;
    if (GetDiskFreeSpaceExW(local_appdata, &available, NULL, NULL)) {
        g_docker_disk_free_bytes = available.QuadPart;
    }
}

static void analyze_system(void) {
    wchar_t path[MAX_PATH * 4];
    g_winget_present = find_program(L"winget.exe", path, (DWORD)(sizeof(path) / sizeof(wchar_t)));
    g_docker_present = get_docker_cli(path, (DWORD)(sizeof(path) / sizeof(wchar_t))) ||
                       get_docker_desktop(path, (DWORD)(sizeof(path) / sizeof(wchar_t)));
    g_git_present = find_program(L"git.exe", path, (DWORD)(sizeof(path) / sizeof(wchar_t)));
    g_vscode_present = get_vscode(path, (DWORD)(sizeof(path) / sizeof(wchar_t)));
    refresh_docker_disk_free_space();

    set_dependency_control(g_docker, L"Docker Desktop (requis)", g_docker_present, g_winget_present);
    set_dependency_control(g_git, L"Git (optionnel)", g_git_present, g_winget_present);
    set_dependency_control(g_vscode, L"Visual Studio Code (optionnel)", g_vscode_present, g_winget_present);

    wchar_t summary[512];
    _snwprintf(summary, sizeof(summary) / sizeof(wchar_t),
               L"Analyse : winget %ls ; Docker %ls ; Git %ls ; VS Code %ls.\r\n",
               g_winget_present ? L"détecté" : L"absent",
               g_docker_present ? L"détecté" : L"absent",
               g_git_present ? L"détecté" : L"absent",
               g_vscode_present ? L"détecté" : L"absent");
    append_log_control(summary);
    if (g_docker_disk_free_bytes > 0) {
        wchar_t disk_summary[256];
        unsigned long long free_mib = (unsigned long long)(g_docker_disk_free_bytes / (1024ULL * 1024ULL));
        _snwprintf(disk_summary, sizeof(disk_summary) / sizeof(wchar_t),
                   L"Espace libre sur le disque de LOCALAPPDATA (emplacement Docker par défaut) : %llu Mo.\r\n", free_mib);
        append_log_control(disk_summary);
        if (g_docker_disk_free_bytes < 5ULL * 1024ULL * 1024ULL * 1024ULL) {
            append_log_control(L"Avertissement : moins de 5 Go sont disponibles. Libérez idéalement au moins 10 Go avant les constructions Docker.\r\n");
        }
    }
    if (!g_winget_present) {
        append_log_control(L"winget est absent. Les cases d'installation tierce restent désactivées ; utilisez Microsoft App Installer.\r\n");
    }
    update_uninstall_control();
}

static int decode_and_post(const char *buffer, DWORD length) {
    if (!length) return 0;
    int count = MultiByteToWideChar(CP_UTF8, 0, buffer, (int)length, NULL, 0);
    UINT codepage = CP_UTF8;
    if (count <= 0) {
        codepage = CP_ACP;
        count = MultiByteToWideChar(codepage, 0, buffer, (int)length, NULL, 0);
    }
    if (count <= 0) return -1;
    wchar_t *wide = HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, ((size_t)count + 1) * sizeof(wchar_t));
    if (!wide) return -1;
    MultiByteToWideChar(codepage, 0, buffer, (int)length, wide, count);
    PostMessageW(g_main, WM_HDP_LOG, 1, (LPARAM)wide);
    return 0;
}

static DWORD run_process_capture_timeout(const wchar_t *application, const wchar_t *arguments,
                                         const wchar_t *working_directory, DWORD timeout_ms) {
    SECURITY_ATTRIBUTES security = { sizeof(SECURITY_ATTRIBUTES), NULL, TRUE };
    HANDLE read_pipe = NULL;
    HANDLE write_pipe = NULL;
    if (!CreatePipe(&read_pipe, &write_pipe, &security, 0)) return ERROR_PIPE_NOT_CONNECTED;
    SetHandleInformation(read_pipe, HANDLE_FLAG_INHERIT, 0);

    STARTUPINFOW startup;
    PROCESS_INFORMATION process;
    ZeroMemory(&startup, sizeof(startup));
    ZeroMemory(&process, sizeof(process));
    startup.cb = sizeof(startup);
    startup.dwFlags = STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
    startup.wShowWindow = SW_HIDE;
    startup.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
    startup.hStdOutput = write_pipe;
    startup.hStdError = write_pipe;

    size_t cmd_length = wcslen(application) + wcslen(arguments) + 8;
    wchar_t *command = HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, cmd_length * sizeof(wchar_t));
    if (!command) {
        CloseHandle(read_pipe);
        CloseHandle(write_pipe);
        return ERROR_NOT_ENOUGH_MEMORY;
    }
    _snwprintf(command, cmd_length, L"\"%ls\" %ls", application, arguments);
    BOOL created = CreateProcessW(application, command, NULL, NULL, TRUE,
                                  CREATE_NO_WINDOW | CREATE_UNICODE_ENVIRONMENT | CREATE_SUSPENDED,
                                  NULL, working_directory, &startup, &process);
    HeapFree(GetProcessHeap(), 0, command);
    if (!created) {
        DWORD error = GetLastError();
        CloseHandle(write_pipe);
        CloseHandle(read_pipe);
        return error;
    }

    HANDLE job = CreateJobObjectW(NULL, NULL);
    BOOL job_assigned = FALSE;
    if (job) {
        JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits;
        ZeroMemory(&limits, sizeof(limits));
        limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        if (SetInformationJobObject(job, JobObjectExtendedLimitInformation, &limits, sizeof(limits))) {
            job_assigned = AssignProcessToJobObject(job, process.hProcess);
        }
    }
    ResumeThread(process.hThread);
    CloseHandle(write_pipe);

    char buffer[4096];
    DWORD received = 0;
    ULONGLONG last_display = 0;
    ULONGLONG started = GetTickCount64();
    ULONGLONG next_heartbeat = 30ULL * 1000ULL;
    DWORD exit_code = ERROR_GEN_FAILURE;
    BOOL cancelled = FALSE;
    BOOL timed_out = FALSE;

    for (;;) {
        DWORD available = 0;
        if (PeekNamedPipe(read_pipe, NULL, 0, NULL, &available, NULL)) {
            while (available > 0) {
                DWORD requested = available < sizeof(buffer) ? available : (DWORD)sizeof(buffer);
                if (!ReadFile(read_pipe, buffer, requested, &received, NULL) || received == 0) break;
                append_log_bytes(buffer, received);
                ULONGLONG now = GetTickCount64();
                if (last_display == 0 || now - last_display >= 1000) {
                    decode_and_post(buffer, received);
                    last_display = now;
                }
                if (!PeekNamedPipe(read_pipe, NULL, 0, NULL, &available, NULL)) break;
            }
        }

        DWORD wait_result = WaitForSingleObject(process.hProcess, 0);
        if (wait_result == WAIT_OBJECT_0) {
            GetExitCodeProcess(process.hProcess, &exit_code);
            break;
        }
        if (wait_result == WAIT_FAILED) {
            exit_code = GetLastError();
            break;
        }

        ULONGLONG elapsed = GetTickCount64() - started;
        if (cancel_requested()) {
            cancelled = TRUE;
        } else if (timeout_ms > 0 && elapsed >= timeout_ms) {
            timed_out = TRUE;
        }
        if (cancelled || timed_out) {
            if (job_assigned) TerminateJobObject(job, cancelled ? ERROR_CANCELLED : ERROR_TIMEOUT);
            else TerminateProcess(process.hProcess, cancelled ? ERROR_CANCELLED : ERROR_TIMEOUT);
            WaitForSingleObject(process.hProcess, 5000);
            exit_code = cancelled ? ERROR_CANCELLED : ERROR_TIMEOUT;
            break;
        }
        if (elapsed >= next_heartbeat) {
            wchar_t heartbeat[320];
            _snwprintf(heartbeat, sizeof(heartbeat) / sizeof(wchar_t),
                       L"Commande toujours active : %llu secondes écoulées. Le journal brut continue d'être enregistré.\r\n",
                       (unsigned long long)(elapsed / 1000ULL));
            post_log(heartbeat);
            next_heartbeat += 30ULL * 1000ULL;
        }
        Sleep(200);
    }

    CloseHandle(read_pipe);
    if (job) CloseHandle(job);
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return exit_code;
}

static DWORD run_process_quiet_timeout(const wchar_t *application, const wchar_t *arguments,
                                       const wchar_t *working_directory, DWORD timeout_ms,
                                       BOOL *timed_out) {
    if (timed_out) *timed_out = FALSE;
    SECURITY_ATTRIBUTES security = { sizeof(SECURITY_ATTRIBUTES), NULL, TRUE };
    HANDLE null_file = CreateFileW(L"NUL", GENERIC_READ | GENERIC_WRITE,
                                   FILE_SHARE_READ | FILE_SHARE_WRITE,
                                   &security, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (null_file == INVALID_HANDLE_VALUE) return GetLastError();
    STARTUPINFOW startup;
    PROCESS_INFORMATION process;
    ZeroMemory(&startup, sizeof(startup));
    ZeroMemory(&process, sizeof(process));
    startup.cb = sizeof(startup);
    startup.dwFlags = STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
    startup.wShowWindow = SW_HIDE;
    startup.hStdInput = null_file;
    startup.hStdOutput = null_file;
    startup.hStdError = null_file;

    size_t cmd_length = wcslen(application) + wcslen(arguments) + 8;
    wchar_t *command = HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, cmd_length * sizeof(wchar_t));
    if (!command) {
        CloseHandle(null_file);
        return ERROR_NOT_ENOUGH_MEMORY;
    }
    _snwprintf(command, cmd_length, L"\"%ls\" %ls", application, arguments);
    BOOL created = CreateProcessW(application, command, NULL, NULL, TRUE,
                                  CREATE_NO_WINDOW | CREATE_UNICODE_ENVIRONMENT,
                                  NULL, working_directory, &startup, &process);
    HeapFree(GetProcessHeap(), 0, command);
    CloseHandle(null_file);
    if (!created) return GetLastError();

    DWORD exit_code = ERROR_GEN_FAILURE;
    DWORD wait_result = WaitForSingleObject(process.hProcess, timeout_ms);
    if (wait_result == WAIT_OBJECT_0) {
        GetExitCodeProcess(process.hProcess, &exit_code);
    } else if (wait_result == WAIT_TIMEOUT) {
        if (timed_out) *timed_out = TRUE;
        TerminateProcess(process.hProcess, ERROR_TIMEOUT);
        WaitForSingleObject(process.hProcess, 2000);
        exit_code = ERROR_TIMEOUT;
    } else {
        exit_code = GetLastError();
    }
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return exit_code;
}

static BOOL install_winget_package(const wchar_t *package_id, const wchar_t *display_name) {
    wchar_t winget[MAX_PATH * 4];
    if (!find_program(L"winget.exe", winget, (DWORD)(sizeof(winget) / sizeof(wchar_t)))) return FALSE;
    wchar_t args[1024];
    _snwprintf(args, sizeof(args) / sizeof(wchar_t),
               L"install --id %ls --exact --source winget --accept-source-agreements --accept-package-agreements --disable-interactivity",
               package_id);
    wchar_t message[512];
    _snwprintf(message, sizeof(message) / sizeof(wchar_t), L"Installation de %ls via winget…\r\n", display_name);
    post_log(message);
    DWORD result = run_process_capture_timeout(winget, args, NULL, WINGET_TIMEOUT_MS);
    if (result != 0) {
        _snwprintf(message, sizeof(message) / sizeof(wchar_t), L"Échec de %ls : winget a retourné le code %lu.\r\n", display_name, result);
        post_log(message);
        return FALSE;
    }
    _snwprintf(message, sizeof(message) / sizeof(wchar_t), L"%ls installé.\r\n", display_name);
    post_log(message);
    return TRUE;
}

static BOOL ensure_directory(const wchar_t *path) {
    int result = SHCreateDirectoryExW(NULL, path, NULL);
    return result == ERROR_SUCCESS || result == ERROR_ALREADY_EXISTS || directory_exists(path);
}

static BOOL utf8_path_to_wide(const char *source, wchar_t *destination, int capacity) {
    int count = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, source, -1, destination, capacity);
    if (count <= 0) return FALSE;
    for (wchar_t *cursor = destination; *cursor; cursor++) {
        if (*cursor == L'/') *cursor = L'\\';
    }
    return TRUE;
}

static BOOL write_binary_file(const wchar_t *path, const unsigned char *data, size_t size) {
    wchar_t parent[MAX_PATH * 4];
    wcsncpy(parent, path, (sizeof(parent) / sizeof(wchar_t)) - 1);
    parent[(sizeof(parent) / sizeof(wchar_t)) - 1] = 0;
    wchar_t *separator = wcsrchr(parent, L'\\');
    if (separator) {
        *separator = 0;
        if (!ensure_directory(parent)) return FALSE;
    }
    HANDLE file = CreateFileW(path, GENERIC_WRITE, FILE_SHARE_READ, NULL, CREATE_ALWAYS,
                              FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) return FALSE;
    size_t offset = 0;
    BOOL ok = TRUE;
    while (offset < size) {
        DWORD chunk = (DWORD)((size - offset) > 1024 * 1024 ? 1024 * 1024 : (size - offset));
        DWORD written = 0;
        if (!WriteFile(file, data + offset, chunk, &written, NULL) || written != chunk) {
            ok = FALSE;
            break;
        }
        offset += written;
    }
    CloseHandle(file);
    return ok;
}

static BOOL deploy_payload(const wchar_t *install_dir) {
    if (!ensure_directory(install_dir)) return FALSE;
    for (size_t index = 0; index < g_payload_file_count; index++) {
        wchar_t relative[MAX_PATH * 2];
        wchar_t destination[MAX_PATH * 4];
        if (!utf8_path_to_wide(g_payload_files[index].path, relative, (int)(sizeof(relative) / sizeof(wchar_t)))) return FALSE;
        _snwprintf(destination, sizeof(destination) / sizeof(wchar_t), L"%ls\\%ls", install_dir, relative);
        if (!write_binary_file(destination, g_payload_files[index].data, g_payload_files[index].size)) return FALSE;
    }
    return TRUE;
}

static char *read_file_bytes(const wchar_t *path, DWORD *size_out) {
    HANDLE file = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL,
                              OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) return NULL;
    LARGE_INTEGER size;
    if (!GetFileSizeEx(file, &size) || size.QuadPart < 0 || size.QuadPart > 1024 * 1024) {
        CloseHandle(file);
        return NULL;
    }
    char *data = HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, (size_t)size.QuadPart + 1);
    if (!data) {
        CloseHandle(file);
        return NULL;
    }
    DWORD received = 0;
    if (!ReadFile(file, data, (DWORD)size.QuadPart, &received, NULL)) {
        HeapFree(GetProcessHeap(), 0, data);
        CloseHandle(file);
        return NULL;
    }
    CloseHandle(file);
    data[received] = 0;
    *size_out = received;
    return data;
}

static BOOL write_installation_marker(const wchar_t *install_dir) {
    wchar_t marker_path[MAX_PATH * 4];
    _snwprintf(marker_path, sizeof(marker_path) / sizeof(wchar_t),
               L"%ls\\%ls", install_dir, INSTALLATION_MARKER_NAME);
    const char marker[] = INSTALLATION_MARKER_CONTENT;
    return write_binary_file(marker_path, (const unsigned char *)marker, sizeof(marker) - 1);
}

static BOOL installation_marker_is_valid(const wchar_t *install_dir) {
    wchar_t marker_path[MAX_PATH * 4];
    _snwprintf(marker_path, sizeof(marker_path) / sizeof(wchar_t),
               L"%ls\\%ls", install_dir, INSTALLATION_MARKER_NAME);
    DWORD size = 0;
    char *data = read_file_bytes(marker_path, &size);
    if (!data) return FALSE;
    const char expected[] = INSTALLATION_MARKER_CONTENT;
    BOOL valid = size == sizeof(expected) - 1 &&
                 memcmp(data, expected, sizeof(expected) - 1) == 0;
    HeapFree(GetProcessHeap(), 0, data);
    return valid;
}

static BOOL installation_path_is_safe(const wchar_t *install_dir) {
    size_t length = wcslen(install_dir);
    if (length <= 3 || length >= MAX_PATH * 4 - 64) return FALSE;
    wchar_t canonical[MAX_PATH * 4];
    DWORD count = GetFullPathNameW(install_dir,
                                   (DWORD)(sizeof(canonical) / sizeof(wchar_t)),
                                   canonical, NULL);
    if (!count || count >= sizeof(canonical) / sizeof(wchar_t) ||
        _wcsicmp(canonical, install_dir) != 0) return FALSE;
    wchar_t compose[MAX_PATH * 4];
    wchar_t launcher[MAX_PATH * 4];
    wchar_t env_path[MAX_PATH * 4];
    _snwprintf(compose, sizeof(compose) / sizeof(wchar_t), L"%ls\\compose.yaml", install_dir);
    _snwprintf(launcher, sizeof(launcher) / sizeof(wchar_t), L"%ls\\start-hdp.cmd", install_dir);
    _snwprintf(env_path, sizeof(env_path) / sizeof(wchar_t), L"%ls\\.env", install_dir);
    return file_exists(compose) && file_exists(launcher) && file_exists(env_path) &&
           installation_marker_is_valid(install_dir);
}

static BOOL payload_relative_path_is_safe(const wchar_t *relative) {
    if (!relative[0] || relative[0] == L'\\' || wcschr(relative, L':')) return FALSE;
    const wchar_t *segment = relative;
    for (const wchar_t *cursor = relative; ; cursor++) {
        if (*cursor == L'\\' || *cursor == 0) {
            size_t length = (size_t)(cursor - segment);
            if (!length || (length == 1 && segment[0] == L'.') ||
                (length == 2 && segment[0] == L'.' && segment[1] == L'.')) return FALSE;
            if (!*cursor) break;
            segment = cursor + 1;
        }
    }
    return TRUE;
}

static BOOL remove_managed_payload(const wchar_t *install_dir,
                                   size_t *removed_out, size_t *missing_out) {
    size_t removed = 0;
    size_t missing = 0;
    BOOL success = TRUE;
    for (size_t index = 0; index < g_payload_file_count; index++) {
        wchar_t relative[MAX_PATH * 2];
        wchar_t destination[MAX_PATH * 4];
        if (!utf8_path_to_wide(g_payload_files[index].path, relative,
                               (int)(sizeof(relative) / sizeof(wchar_t))) ||
            !payload_relative_path_is_safe(relative)) {
            post_log(L"Entrée du payload non sûre : désinstallation interrompue.\r\n");
            success = FALSE;
            continue;
        }
        _snwprintf(destination, sizeof(destination) / sizeof(wchar_t),
                   L"%ls\\%ls", install_dir, relative);
        if (DeleteFileW(destination)) {
            removed++;
            continue;
        }
        DWORD error = GetLastError();
        if (error == ERROR_FILE_NOT_FOUND || error == ERROR_PATH_NOT_FOUND) {
            missing++;
            continue;
        }
        wchar_t message[MAX_PATH * 4 + 160];
        _snwprintf(message, sizeof(message) / sizeof(wchar_t),
                   L"Fichier géré non supprimé (code %lu) : %ls\r\n", error, destination);
        post_log(message);
        success = FALSE;
    }
    if (removed_out) *removed_out = removed;
    if (missing_out) *missing_out = missing;
    return success;
}

static BOOL extract_env_value(const char *data, const char *key, char *value, size_t capacity) {
    size_t key_length = strlen(key);
    const char *cursor = data;
    while (cursor && *cursor) {
        const char *line_end = strpbrk(cursor, "\r\n");
        size_t line_length = line_end ? (size_t)(line_end - cursor) : strlen(cursor);
        if (line_length > key_length + 1 && !strncmp(cursor, key, key_length) && cursor[key_length] == '=') {
            size_t value_length = line_length - key_length - 1;
            if (value_length >= capacity) value_length = capacity - 1;
            memcpy(value, cursor + key_length + 1, value_length);
            value[value_length] = 0;
            return TRUE;
        }
        if (!line_end) break;
        cursor = line_end + 1;
        if (*cursor == '\n' && line_end[0] == '\r') cursor++;
    }
    return FALSE;
}

static BOOL ensure_winsock(void) {
    if (g_winsock_initialized) return TRUE;
    WSADATA data;
    if (WSAStartup(MAKEWORD(2, 2), &data) != 0) return FALSE;
    g_winsock_initialized = TRUE;
    return TRUE;
}

static BOOL port_is_available(USHORT port, int *socket_error) {
    if (socket_error) *socket_error = 0;
    if (!ensure_winsock()) {
        if (socket_error) *socket_error = WSASYSNOTREADY;
        return FALSE;
    }

    SOCKET probe = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (probe == INVALID_SOCKET) {
        if (socket_error) *socket_error = WSAGetLastError();
        return FALSE;
    }

    BOOL exclusive = TRUE;
    setsockopt(probe, SOL_SOCKET, SO_EXCLUSIVEADDRUSE,
               (const char *)&exclusive, (int)sizeof(exclusive));
    struct sockaddr_in address;
    ZeroMemory(&address, sizeof(address));
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    address.sin_port = htons(port);

    BOOL available = bind(probe, (const struct sockaddr *)&address, sizeof(address)) == 0;
    if (!available && socket_error) *socket_error = WSAGetLastError();
    closesocket(probe);
    return available;
}

static USHORT parse_port(const char *text) {
    if (!text || !*text) return 0;
    char *end = NULL;
    unsigned long value = strtoul(text, &end, 10);
    if (!end || *end || value < 1024 || value > 65535) return 0;
    return (USHORT)value;
}

static USHORT read_existing_host_port(const wchar_t *install_dir) {
    wchar_t env_path[MAX_PATH * 4];
    _snwprintf(env_path, sizeof(env_path) / sizeof(wchar_t), L"%ls\\.env", install_dir);
    DWORD size = 0;
    char *existing = read_file_bytes(env_path, &size);
    if (!existing) return 0;
    char value[32] = {0};
    extract_env_value(existing, "HDP_PORT", value, sizeof(value));
    HeapFree(GetProcessHeap(), 0, existing);
    return parse_port(value);
}

static USHORT choose_host_port(const wchar_t *install_dir) {
    USHORT existing = read_existing_host_port(install_dir);
    int error = 0;
    if (existing) {
        if (http_is_healthy(existing) || port_is_available(existing, &error)) {
            wchar_t message[256];
            _snwprintf(message, sizeof(message) / sizeof(wchar_t),
                       L"Port local %u conservé depuis la configuration existante.\r\n", existing);
            post_log(message);
            return existing;
        }
        wchar_t message[320];
        _snwprintf(message, sizeof(message) / sizeof(wchar_t),
                   L"Le port configuré %u n'est plus disponible (erreur Winsock %d). Recherche d'un autre port local.\r\n",
                   existing, error);
        post_log(message);
    }

    if ((!existing || existing != 8080) && port_is_available(8080, &error)) {
        post_log(L"Port local 8080 disponible.\r\n");
        return 8080;
    }
    if (!existing || existing != 8080) {
        wchar_t message[256];
        _snwprintf(message, sizeof(message) / sizeof(wchar_t),
                   L"Le port Windows 8080 est indisponible (erreur Winsock %d). Sélection automatique d'un port de remplacement.\r\n",
                   error);
        post_log(message);
    }

    for (USHORT candidate = 18080; candidate < 18280; candidate++) {
        if (candidate != existing && port_is_available(candidate, &error)) {
            wchar_t message[256];
            _snwprintf(message, sizeof(message) / sizeof(wchar_t),
                       L"Port local %u sélectionné automatiquement pour l'interface HDP.\r\n", candidate);
            post_log(message);
            return candidate;
        }
    }
    post_log(L"Aucun port local disponible n'a été trouvé entre 18080 et 18279.\r\n");
    return 0;
}

static BOOL generate_secret(char *output, size_t capacity) {
    if (capacity < 49) return FALSE;
    unsigned char random[24];
    if (BCryptGenRandom(NULL, random, sizeof(random), BCRYPT_USE_SYSTEM_PREFERRED_RNG) != 0) return FALSE;
    static const char hex[] = "0123456789abcdef";
    for (size_t index = 0; index < sizeof(random); index++) {
        output[index * 2] = hex[random[index] >> 4];
        output[index * 2 + 1] = hex[random[index] & 15];
    }
    output[48] = 0;
    return TRUE;
}

static BOOL appname_is_valid(const wchar_t *appname) {
    for (const wchar_t *cursor = appname; *cursor; cursor++) {
        wchar_t c = *cursor;
        if (!((c >= L'a' && c <= L'z') || (c >= L'A' && c <= L'Z') ||
              (c >= L'0' && c <= L'9') || c == L'-' || c == L'_' || c == L'.')) return FALSE;
    }
    return TRUE;
}

static BOOL secret_line_is_valid(const wchar_t *secret) {
    for (const wchar_t *cursor = secret; *cursor; cursor++) {
        if (*cursor == L'\r' || *cursor == L'\n') return FALSE;
    }
    return TRUE;
}

static BOOL is_managed_environment_line(const char *line, size_t length) {
    static const char *keys[] = {
        "POSTGRES_PASSWORD", "RELIEFWEB_APPNAME", "HDX_HAPI_APP_IDENTIFIER",
        "GITHUB_TOKEN", "HDP_LOCAL_TOKEN", "HDP_SQL_PASSWORD", "HDP_PORT",
        "HDP_AUTH_MODE", "HDP_WEBAUTHN_RP_ID", "HDP_WEBAUTHN_ORIGIN",
        "HDP_COOKIE_SECURE", "HDP_ALLOWED_HOSTS"
    };
    for (size_t index = 0; index < sizeof(keys) / sizeof(keys[0]); index++) {
        size_t key_length = strlen(keys[index]);
        if (length > key_length && line[key_length] == '=' &&
            !strncmp(line, keys[index], key_length)) return TRUE;
    }
    return FALSE;
}

static BOOL append_environment_bytes(char *output, size_t capacity, size_t *used,
                                     const char *data, size_t length) {
    if (*used >= capacity || length > capacity - *used - 1) return FALSE;
    memcpy(output + *used, data, length);
    *used += length;
    output[*used] = 0;
    return TRUE;
}

static BOOL write_environment(const wchar_t *install_dir, const wchar_t *reliefweb_appname,
                              const wchar_t *github_token, USHORT host_port) {
    wchar_t env_path[MAX_PATH * 4];
    _snwprintf(env_path, sizeof(env_path) / sizeof(wchar_t), L"%ls\\.env", install_dir);
    char password[128] = {0};
    char existing_appname[256] = {0};
    char existing_hapi_identifier[512] = {0};
    char existing_github_token[2048] = {0};
    char local_token[128] = {0};
    char sql_password[128] = {0};
    DWORD existing_size = 0;
    char *existing = read_file_bytes(env_path, &existing_size);
    if (existing) {
        wchar_t backup_path[MAX_PATH * 4];
        _snwprintf(backup_path, sizeof(backup_path) / sizeof(wchar_t),
                   L"%ls\\.env.backup-before-v6.0.0", install_dir);
        if (!CopyFileW(env_path, backup_path, FALSE)) {
            HeapFree(GetProcessHeap(), 0, existing);
            return FALSE;
        }
        post_log(L"Sauvegarde de .env créée avant la mise à niveau.\r\n");
        extract_env_value(existing, "POSTGRES_PASSWORD", password, sizeof(password));
        extract_env_value(existing, "RELIEFWEB_APPNAME", existing_appname, sizeof(existing_appname));
        extract_env_value(existing, "HDX_HAPI_APP_IDENTIFIER", existing_hapi_identifier,
                          sizeof(existing_hapi_identifier));
        extract_env_value(existing, "GITHUB_TOKEN", existing_github_token, sizeof(existing_github_token));
        extract_env_value(existing, "HDP_LOCAL_TOKEN", local_token, sizeof(local_token));
        extract_env_value(existing, "HDP_SQL_PASSWORD", sql_password, sizeof(sql_password));
    }
    if (!password[0] && !generate_secret(password, sizeof(password))) return FALSE;
    if (!local_token[0] && !generate_secret(local_token, sizeof(local_token))) return FALSE;
    if (!sql_password[0] && !generate_secret(sql_password, sizeof(sql_password))) return FALSE;

    char appname_utf8[512] = {0};
    char github_token_utf8[2048] = {0};
    if (reliefweb_appname[0]) {
        WideCharToMultiByte(CP_UTF8, 0, reliefweb_appname, -1, appname_utf8, sizeof(appname_utf8), NULL, NULL);
    } else if (existing_appname[0]) {
        strncpy(appname_utf8, existing_appname, sizeof(appname_utf8) - 1);
    }
    if (github_token[0]) {
        if (!WideCharToMultiByte(CP_UTF8, 0, github_token, -1, github_token_utf8,
                                 sizeof(github_token_utf8), NULL, NULL)) return FALSE;
    } else if (existing_github_token[0]) {
        strncpy(github_token_utf8, existing_github_token, sizeof(github_token_utf8) - 1);
    }
    size_t capacity = (size_t)existing_size + 4096;
    char *content = HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, capacity);
    if (!content) {
        if (existing) HeapFree(GetProcessHeap(), 0, existing);
        return FALSE;
    }
    size_t used = 0;
    const char *cursor = existing;
    BOOL ok = TRUE;
    while (cursor && *cursor && ok) {
        const char *line_end = strpbrk(cursor, "\r\n");
        size_t line_length = line_end ? (size_t)(line_end - cursor) : strlen(cursor);
        if (!is_managed_environment_line(cursor, line_length)) {
            ok = append_environment_bytes(content, capacity, &used, cursor, line_length) &&
                 append_environment_bytes(content, capacity, &used, "\r\n", 2);
        }
        if (!line_end) break;
        cursor = line_end + 1;
        if (line_end[0] == '\r' && *cursor == '\n') cursor++;
    }
    char managed[4096];
    int managed_length = _snprintf(
        managed, sizeof(managed),
        "POSTGRES_PASSWORD=%s\r\nRELIEFWEB_APPNAME=%s\r\n"
        "HDX_HAPI_APP_IDENTIFIER=%s\r\nGITHUB_TOKEN=%s\r\n"
        "HDP_LOCAL_TOKEN=%s\r\nHDP_SQL_PASSWORD=%s\r\nHDP_PORT=%u\r\n"
        "HDP_AUTH_MODE=passkey\r\nHDP_WEBAUTHN_RP_ID=localhost\r\n"
        "HDP_WEBAUTHN_ORIGIN=http://localhost:%u\r\nHDP_COOKIE_SECURE=false\r\n"
        "HDP_ALLOWED_HOSTS=localhost,127.0.0.1,api\r\n",
        password, appname_utf8, existing_hapi_identifier, github_token_utf8,
        local_token, sql_password, host_port, host_port
    );
    if (managed_length <= 0 || managed_length >= (int)sizeof(managed)) ok = FALSE;
    if (ok) {
        ok = append_environment_bytes(
            content, capacity, &used, managed, (size_t)managed_length
        );
    }
    if (existing) HeapFree(GetProcessHeap(), 0, existing);
    if (ok) ok = write_binary_file(env_path, (const unsigned char *)content, used);
    HeapFree(GetProcessHeap(), 0, content);
    return ok;
}

static DWORD probe_docker_engine(const wchar_t *docker, BOOL *timed_out) {
    return run_process_quiet_timeout(
        docker, L"version --format \"{{.Server.Version}}\"", NULL, 5000, timed_out);
}

static void log_wsl_status(void) {
    wchar_t wsl[MAX_PATH * 4];
    if (!find_program(L"wsl.exe", wsl, (DWORD)(sizeof(wsl) / sizeof(wchar_t)))) {
        post_log(L"WSL n'a pas été trouvé. Docker Desktop peut demander l'activation de WSL 2 ou un redémarrage de Windows.\r\n");
        return;
    }
    BOOL timed_out = FALSE;
    DWORD result = run_process_quiet_timeout(wsl, L"--status", NULL, 10000, &timed_out);
    if (result == 0) {
        post_log(L"WSL répond correctement.\r\n");
    } else if (timed_out) {
        post_log(L"La vérification de WSL a dépassé 10 secondes. Docker Desktop peut attendre la fin de l'initialisation WSL 2.\r\n");
    } else {
        wchar_t message[256];
        _snwprintf(message, sizeof(message) / sizeof(wchar_t),
                   L"WSL a retourné le code %lu. Docker Desktop peut demander une mise à jour de WSL 2 ou un redémarrage.\r\n",
                   result);
        post_log(message);
    }
}

static BOOL launch_docker_desktop(const wchar_t *docker) {
    wchar_t desktop[MAX_PATH * 4];
    if (get_docker_desktop(desktop, (DWORD)(sizeof(desktop) / sizeof(wchar_t)))) {
        post_log(L"Démarrage de Docker Desktop…\r\n");
        HINSTANCE launch_result = ShellExecuteW(NULL, L"open", desktop, NULL, NULL, SW_SHOWNORMAL);
        if ((INT_PTR)launch_result > 32) return TRUE;

        wchar_t message[256];
        _snwprintf(message, sizeof(message) / sizeof(wchar_t),
                   L"Windows n'a pas pu ouvrir Docker Desktop (code ShellExecute %lld). Tentative avec la commande Docker Desktop.\r\n",
                   (long long)(INT_PTR)launch_result);
        post_log(message);
    } else {
        post_log(L"L'exécutable graphique Docker Desktop n'a pas été trouvé ; tentative avec la commande Docker Desktop.\r\n");
    }

    BOOL timed_out = FALSE;
    DWORD result = run_process_quiet_timeout(
        docker, L"desktop start --detach --timeout 15", NULL, 20000, &timed_out);
    if (result == 0) {
        post_log(L"La commande Docker Desktop a accepté la demande de démarrage.\r\n");
        return TRUE;
    }
    if (timed_out) {
        post_log(L"La commande de démarrage Docker Desktop a dépassé 20 secondes.\r\n");
    } else {
        wchar_t message[256];
        _snwprintf(message, sizeof(message) / sizeof(wchar_t),
                   L"La commande de démarrage Docker Desktop a retourné le code %lu.\r\n", result);
        post_log(message);
    }
    return FALSE;
}

static BOOL ensure_docker_ready(wchar_t *docker, DWORD capacity) {
    if (!get_docker_cli(docker, capacity)) return FALSE;
    BOOL initial_timed_out = FALSE;
    DWORD initial_result = probe_docker_engine(docker, &initial_timed_out);
    if (initial_result == 0) return TRUE;
    if (initial_timed_out) {
        post_log(L"La première vérification du moteur Docker a dépassé 5 secondes ; la sonde a été arrêtée pour éviter un nouveau gel.\r\n");
    }

    log_wsl_status();
    if (!launch_docker_desktop(docker)) return FALSE;

    post_status(L"Attente du moteur Docker Desktop — terminez l'écran Docker s'il demande une action", 48);
    post_log(L"Docker Desktop a été ouvert. Lors du premier démarrage, lisez puis acceptez ses conditions dans sa propre fenêtre si vous souhaitez continuer ; aucun accord n'est accepté automatiquement par HDP.\r\n");
    PostMessageW(g_main, WM_HDP_DOCKER_ACTION, 0, 0);

    ULONGLONG started = GetTickCount64();
    DWORD next_log_seconds = 30;
    DWORD timed_out_probes = 0;
    DWORD last_result = initial_result;
    while (GetTickCount64() - started < 6ULL * 60ULL * 1000ULL) {
        if (cancel_requested()) {
            post_log(L"Attente de Docker annulée par l'utilisateur.\r\n");
            return FALSE;
        }
        BOOL probe_timed_out = FALSE;
        last_result = probe_docker_engine(docker, &probe_timed_out);
        if (last_result == 0) {
            post_log(L"Le moteur Docker Desktop répond.\r\n");
            return TRUE;
        }
        if (probe_timed_out) timed_out_probes++;

        DWORD elapsed_seconds = (DWORD)((GetTickCount64() - started) / 1000);
        if (elapsed_seconds >= next_log_seconds) {
            wchar_t message[320];
            _snwprintf(message, sizeof(message) / sizeof(wchar_t),
                       L"Toujours en attente du moteur Docker : %lu secondes écoulées ; dernière sonde = code %lu ; sondes interrompues à 5 s = %lu.\r\n",
                       elapsed_seconds, last_result, timed_out_probes);
            post_log(message);
            next_log_seconds += 30;
        }
        Sleep(2000);
    }

    wchar_t failure[512];
    _snwprintf(failure, sizeof(failure) / sizeof(wchar_t),
               L"Le moteur Docker n'a pas répondu dans les 6 minutes. Dernière sonde = code %lu ; sondes interrompues = %lu. Ouvrez Docker Desktop, terminez l'assistant initial ou la mise à jour WSL 2 demandée, puis relancez HDP. Les fichiers et le cache Docker existants sont conservés.\r\n",
               last_result, timed_out_probes);
    post_log(failure);
    return FALSE;
}

static BOOL http_is_healthy(USHORT port) {
    BOOL ok = FALSE;
    HINTERNET session = WinHttpOpen(L"HDP-Installer/2.3", WINHTTP_ACCESS_TYPE_NO_PROXY,
                                    WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0);
    if (!session) return FALSE;
    WinHttpSetTimeouts(session, 3000, 3000, 3000, 3000);
    HINTERNET connection = WinHttpConnect(session, L"localhost", port, 0);
    if (connection) {
        HINTERNET request = WinHttpOpenRequest(connection, L"GET", L"/api/health", NULL,
                                               WINHTTP_NO_REFERER, WINHTTP_DEFAULT_ACCEPT_TYPES, 0);
        if (request && WinHttpSendRequest(request, WINHTTP_NO_ADDITIONAL_HEADERS, 0,
                                          WINHTTP_NO_REQUEST_DATA, 0, 0, 0) &&
            WinHttpReceiveResponse(request, NULL)) {
            DWORD status = 0;
            DWORD size = sizeof(status);
            if (WinHttpQueryHeaders(request, WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
                                    NULL, &status, &size, NULL) && status == 200) {
                char body[1024] = {0};
                DWORD total = 0;
                while (total < sizeof(body) - 1) {
                    DWORD received = 0;
                    if (!WinHttpReadData(request, body + total,
                                         (DWORD)(sizeof(body) - 1 - total), &received) || received == 0) break;
                    total += received;
                }
                body[total] = 0;
                ok = strstr(body, "Humanitarian Data Platform") != NULL;
            }
        }
        if (request) WinHttpCloseHandle(request);
        WinHttpCloseHandle(connection);
    }
    WinHttpCloseHandle(session);
    return ok;
}

static void open_url(const wchar_t *url) {
    ShellExecuteW(NULL, L"open", url, NULL, NULL, SW_SHOWNORMAL);
}

static BOOL create_desktop_shortcut(const wchar_t *install_dir, BOOL include_r) {
    wchar_t desktop[MAX_PATH * 4];
    if (FAILED(SHGetFolderPathW(NULL, CSIDL_DESKTOPDIRECTORY | CSIDL_FLAG_CREATE,
                                NULL, SHGFP_TYPE_CURRENT, desktop))) {
        return FALSE;
    }

    wchar_t target[MAX_PATH * 4];
    _snwprintf(target, sizeof(target) / sizeof(wchar_t), L"%ls\\%ls", install_dir,
               include_r ? L"start-hdp-with-r.cmd" : L"start-hdp.cmd");
    if (!file_exists(target)) return FALSE;

    wchar_t shortcut[MAX_PATH * 4];
    _snwprintf(shortcut, sizeof(shortcut) / sizeof(wchar_t),
               L"%ls\\Humanitarian Data Platform.lnk", desktop);

    HRESULT initialized = CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);
    BOOL must_uninitialize = SUCCEEDED(initialized);
    if (initialized == RPC_E_CHANGED_MODE) must_uninitialize = FALSE;
    else if (FAILED(initialized)) return FALSE;

    IShellLinkW *link = NULL;
    HRESULT result = CoCreateInstance(&CLSID_ShellLink, NULL, CLSCTX_INPROC_SERVER,
                                      &IID_IShellLinkW, (void **)&link);
    if (SUCCEEDED(result)) result = IShellLinkW_SetPath(link, target);
    if (SUCCEEDED(result)) result = IShellLinkW_SetWorkingDirectory(link, install_dir);
    if (SUCCEEDED(result)) {
        result = IShellLinkW_SetDescription(
            link, include_r
                ? L"Démarrer Humanitarian Data Platform avec le module R"
                : L"Démarrer Humanitarian Data Platform");
    }
    IPersistFile *persist = NULL;
    if (SUCCEEDED(result)) {
        result = IShellLinkW_QueryInterface(link, &IID_IPersistFile, (void **)&persist);
    }
    if (SUCCEEDED(result)) result = IPersistFile_Save(persist, shortcut, TRUE);
    if (persist) IPersistFile_Release(persist);
    if (link) IShellLinkW_Release(link);
    if (must_uninitialize) CoUninitialize();
    return SUCCEEDED(result);
}

static BOOL remove_managed_desktop_shortcut(const wchar_t *install_dir,
                                            BOOL *found_out, BOOL *removed_out) {
    if (found_out) *found_out = FALSE;
    if (removed_out) *removed_out = FALSE;
    wchar_t desktop[MAX_PATH * 4];
    if (FAILED(SHGetFolderPathW(NULL, CSIDL_DESKTOPDIRECTORY,
                                NULL, SHGFP_TYPE_CURRENT, desktop))) return FALSE;
    wchar_t shortcut[MAX_PATH * 4];
    _snwprintf(shortcut, sizeof(shortcut) / sizeof(wchar_t),
               L"%ls\\Humanitarian Data Platform.lnk", desktop);
    if (!file_exists(shortcut)) return TRUE;
    if (found_out) *found_out = TRUE;

    HRESULT initialized = CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);
    BOOL must_uninitialize = SUCCEEDED(initialized);
    if (initialized == RPC_E_CHANGED_MODE) must_uninitialize = FALSE;
    else if (FAILED(initialized)) return FALSE;

    IShellLinkW *link = NULL;
    IPersistFile *persist = NULL;
    HRESULT result = CoCreateInstance(&CLSID_ShellLink, NULL, CLSCTX_INPROC_SERVER,
                                      &IID_IShellLinkW, (void **)&link);
    if (SUCCEEDED(result)) {
        result = IShellLinkW_QueryInterface(link, &IID_IPersistFile, (void **)&persist);
    }
    if (SUCCEEDED(result)) result = IPersistFile_Load(persist, shortcut, STGM_READ);
    wchar_t target[MAX_PATH * 4] = L"";
    WIN32_FIND_DATAW target_data;
    ZeroMemory(&target_data, sizeof(target_data));
    if (SUCCEEDED(result)) {
        result = IShellLinkW_GetPath(link, target,
                                    (int)(sizeof(target) / sizeof(wchar_t)),
                                    &target_data, SLGP_RAWPATH);
    }
    wchar_t standard[MAX_PATH * 4];
    wchar_t analytics[MAX_PATH * 4];
    _snwprintf(standard, sizeof(standard) / sizeof(wchar_t),
               L"%ls\\start-hdp.cmd", install_dir);
    _snwprintf(analytics, sizeof(analytics) / sizeof(wchar_t),
               L"%ls\\start-hdp-with-r.cmd", install_dir);
    BOOL owned = SUCCEEDED(result) &&
                 (!_wcsicmp(target, standard) || !_wcsicmp(target, analytics));
    if (persist) IPersistFile_Release(persist);
    if (link) IShellLinkW_Release(link);
    if (must_uninitialize) CoUninitialize();
    if (!SUCCEEDED(result)) return FALSE;
    if (!owned) return TRUE;
    if (!DeleteFileW(shortcut)) return FALSE;
    if (removed_out) *removed_out = TRUE;
    return TRUE;
}

static DWORD WINAPI install_thread(LPVOID parameter) {
    InstallOptions *options = (InstallOptions *)parameter;
    BOOL success = FALSE;

    post_status(L"Installation des prérequis sélectionnés…", 10);
    if (options->install_git && !install_winget_package(L"Git.Git", L"Git")) goto done;
    if (options->install_vscode && !install_winget_package(L"Microsoft.VisualStudioCode", L"Visual Studio Code")) goto done;
    if (options->install_docker && !install_winget_package(L"Docker.DockerDesktop", L"Docker Desktop")) goto done;

    post_status(L"Déploiement des fichiers de l'application…", 35);
    post_log(L"Écriture du socle FastAPI, PostgreSQL/PostGIS et R/plumber…\r\n");
    if (!deploy_payload(options->install_dir)) {
        post_log(L"Échec de l'écriture des fichiers. Vérifiez le chemin et les droits d'accès.\r\n");
        goto done;
    }
    options->host_port = choose_host_port(options->install_dir);
    if (!options->host_port) {
        post_log(L"Impossible de sélectionner un port local pour l'interface web.\r\n");
        goto done;
    }
    if (!write_environment(options->install_dir, options->reliefweb_appname,
                           options->github_token, options->host_port)) {
        post_log(L"Échec de la création du fichier de configuration .env.\r\n");
        goto done;
    }
    if (!write_installation_marker(options->install_dir)) {
        post_log(L"Échec de la création du marqueur de gestion HDP. La désinstallation sûre resterait indisponible.\r\n");
        goto done;
    }
    post_log(L"Fichiers installés et configuration locale créée.\r\n");

    post_status(L"Vérification de Docker Desktop…", 48);
    wchar_t docker[MAX_PATH * 4];
    if (!ensure_docker_ready(docker, (DWORD)(sizeof(docker) / sizeof(wchar_t)))) {
        post_log(L"Docker Desktop n'est pas prêt. Un redémarrage de Windows, WSL 2 ou la virtualisation peuvent être nécessaires. Relancez ensuite cet installateur.\r\n");
        goto done;
    }
    post_log(L"Docker Desktop est opérationnel.\r\n");

    wchar_t compose_args[MAX_PATH * 5];

    post_status(L"Téléchargement de PostgreSQL/PostGIS — sortie détaillée limitée pour préserver l'interface", 55);
    post_log(L"Téléchargement silencieux de l'image PostgreSQL/PostGIS. Cette étape peut durer plusieurs minutes au premier lancement.\r\n");
    _snwprintf(compose_args, sizeof(compose_args) / sizeof(wchar_t),
               L"compose -f \"%ls\\compose.yaml\" pull --quiet db", options->install_dir);
    DWORD compose_result = run_process_capture_timeout(
        docker, compose_args, options->install_dir, COMPOSE_PULL_TIMEOUT_MS);
    if (compose_result != 0) {
        wchar_t error[256];
        _snwprintf(error, sizeof(error) / sizeof(wchar_t), L"Le téléchargement PostgreSQL/PostGIS a retourné le code %lu.\r\n", compose_result);
        post_log(error);
        goto done;
    }
    post_log(L"Image PostgreSQL/PostGIS disponible.\r\n");

    post_status(L"Construction des services Python et GitHub", 66);
    post_log(L"Construction silencieuse de l'API et du runner Python sans réseau. Le compteur d'activité confirme que le processus continue.\r\n");
    _snwprintf(compose_args, sizeof(compose_args) / sizeof(wchar_t),
               L"compose -f \"%ls\\compose.yaml\" build --quiet api runner-python", options->install_dir);
    compose_result = run_process_capture_timeout(
        docker, compose_args, options->install_dir, COMPOSE_BUILD_TIMEOUT_MS);
    if (compose_result != 0) {
        wchar_t error[256];
        _snwprintf(error, sizeof(error) / sizeof(wchar_t), L"La construction de l'API Python a retourné le code %lu.\r\n", compose_result);
        post_log(error);
        goto done;
    }
        post_log(L"API Python/FastAPI et runner Python construits.\r\n");

    if (options->install_r_module) {
        post_status(L"Construction du module analytique R — téléchargement supérieur à 300 Mo", 73);
        post_log(L"Le module R a été sélectionné. Son image est volumineuse ; le premier téléchargement peut être long.\r\n");
        _snwprintf(compose_args, sizeof(compose_args) / sizeof(wchar_t),
                   L"compose -f \"%ls\\compose.yaml\" --profile analytics build --quiet r-service runner-r", options->install_dir);
        compose_result = run_process_capture_timeout(
            docker, compose_args, options->install_dir, COMPOSE_BUILD_TIMEOUT_MS);
        if (compose_result != 0) {
            wchar_t error[256];
            _snwprintf(error, sizeof(error) / sizeof(wchar_t), L"La construction du module R a retourné le code %lu.\r\n", compose_result);
            post_log(error);
            goto done;
        }
        post_log(L"Module analytique R construit.\r\n");
    } else {
        post_log(L"Module R différé : le cœur Python/PostGIS sera disponible immédiatement. Relancez l'installateur pour ajouter R ultérieurement.\r\n");
    }

    post_status(L"Démarrage des services locaux", 84);
    if (options->install_r_module) {
        _snwprintf(compose_args, sizeof(compose_args) / sizeof(wchar_t),
                   L"compose -f \"%ls\\compose.yaml\" --profile analytics up -d --no-build db r-service runner-python runner-r api", options->install_dir);
    } else {
        _snwprintf(compose_args, sizeof(compose_args) / sizeof(wchar_t),
                   L"compose -f \"%ls\\compose.yaml\" up -d --no-build db runner-python api", options->install_dir);
    }
    compose_result = run_process_capture_timeout(
        docker, compose_args, options->install_dir, COMPOSE_UP_TIMEOUT_MS);
    if (compose_result != 0) {
        wchar_t error[256];
        _snwprintf(error, sizeof(error) / sizeof(wchar_t), L"Le démarrage Docker Compose a retourné le code %lu.\r\n", compose_result);
        post_log(error);
        _snwprintf(compose_args, sizeof(compose_args) / sizeof(wchar_t),
                   L"compose -f \"%ls\\compose.yaml\" --profile analytics logs --no-color --tail 120", options->install_dir);
        run_process_capture_timeout(docker, compose_args, options->install_dir, COMPOSE_LOGS_TIMEOUT_MS);
        goto done;
    }

    post_status(L"Vérification de l'interface web…", 90);
    for (int attempt = 0; attempt < 100; attempt++) {
        if (cancel_requested()) goto done;
        if (http_is_healthy(options->host_port)) {
            success = TRUE;
            break;
        }
        if (attempt % 5 == 0) post_log(L"Attente du service web local…\r\n");
        Sleep(2000);
    }
    if (!success) {
        post_log(L"Les conteneurs ont démarré, mais l'interface n'a pas répondu dans le délai prévu. Consultez le journal ci-dessus.\r\n");
        _snwprintf(compose_args, sizeof(compose_args) / sizeof(wchar_t),
                   L"compose -f \"%ls\\compose.yaml\" logs --no-color --tail 120", options->install_dir);
        run_process_capture_timeout(docker, compose_args, options->install_dir, COMPOSE_LOGS_TIMEOUT_MS);
        goto done;
    }

    post_status(L"Installation terminée — ouverture du navigateur", 100);
    wchar_t local_url[384];
    _snwprintf(local_url, sizeof(local_url) / sizeof(wchar_t),
               L"http://localhost:%u/", options->host_port);
    wchar_t success_message[512];
    _snwprintf(success_message, sizeof(success_message) / sizeof(wchar_t),
               L"Installation réussie. Interface : %ls\r\n", local_url);
    post_log(success_message);
    if (create_desktop_shortcut(options->install_dir, options->install_r_module)) {
        post_log(L"Raccourci « Humanitarian Data Platform » créé sur le Bureau.\r\n");
    } else {
        post_log(L"Avertissement : le raccourci Bureau n'a pas pu être créé. Utilisez start-hdp.cmd dans le dossier d'installation.\r\n");
    }
    open_url(local_url);

done:
    if (!success) {
        if (cancel_requested()) {
            post_log(L"Installation annulée par l'utilisateur. Les données et volumes existants sont conservés.\r\n");
            post_status(L"Installation annulée — données conservées", 0);
        } else {
            post_status(L"Installation interrompue — consultez le journal", 0);
        }
    }
    HeapFree(GetProcessHeap(), 0, options);
    PostMessageW(g_main, WM_HDP_FINISHED, success ? 1 : 0, 0);
    return 0;
}

static DWORD WINAPI uninstall_thread(LPVOID parameter) {
    InstallOptions *options = (InstallOptions *)parameter;
    BOOL success = FALSE;
    post_status(L"Arrêt contrôlé des services HDP…", 20);
    wchar_t docker[MAX_PATH * 4];
    if (!get_docker_cli(docker, (DWORD)(sizeof(docker) / sizeof(wchar_t)))) {
        post_log(L"Docker CLI est introuvable. Démarrez ou réparez Docker Desktop avant de désinstaller HDP.\r\n");
        goto done;
    }
    wchar_t compose_args[MAX_PATH * 5];
    _snwprintf(compose_args, sizeof(compose_args) / sizeof(wchar_t),
               L"compose -f \"%ls\\compose.yaml\" --profile analytics down --remove-orphans",
               options->install_dir);
    DWORD compose_result = run_process_capture_timeout(
        docker, compose_args, options->install_dir, COMPOSE_UP_TIMEOUT_MS);
    if (compose_result != 0) {
        wchar_t error[320];
        _snwprintf(error, sizeof(error) / sizeof(wchar_t),
                   L"L'arrêt Docker Compose a retourné le code %lu. Aucun fichier HDP n'a été supprimé.\r\n",
                   compose_result);
        post_log(error);
        goto done;
    }
    post_log(L"Services HDP arrêtés sans supprimer les volumes Docker.\r\n");

    post_status(L"Vérification et suppression du raccourci HDP…", 55);
    BOOL shortcut_found = FALSE;
    BOOL shortcut_removed = FALSE;
    if (!remove_managed_desktop_shortcut(options->install_dir,
                                         &shortcut_found, &shortcut_removed)) {
        post_log(L"Le raccourci Bureau n'a pas pu être vérifié ou supprimé. Les fichiers HDP sont conservés.\r\n");
        goto done;
    }
    if (shortcut_removed) {
        post_log(L"Raccourci Bureau HDP vérifié puis supprimé.\r\n");
    } else if (shortcut_found) {
        post_log(L"Un raccourci de même nom ne cible pas cette installation ; il est conservé.\r\n");
    } else {
        post_log(L"Aucun raccourci Bureau HDP n'était présent.\r\n");
    }

    post_status(L"Suppression limitée aux fichiers gérés par HDP…", 75);
    size_t removed = 0;
    size_t missing = 0;
    if (!remove_managed_payload(options->install_dir, &removed, &missing)) {
        post_log(L"Certains fichiers gérés n'ont pas pu être supprimés. Le marqueur HDP est conservé pour reprendre la désinstallation.\r\n");
        goto done;
    }
    wchar_t marker_path[MAX_PATH * 4];
    _snwprintf(marker_path, sizeof(marker_path) / sizeof(wchar_t),
               L"%ls\\%ls", options->install_dir, INSTALLATION_MARKER_NAME);
    if (!DeleteFileW(marker_path)) {
        post_log(L"Le marqueur HDP n'a pas pu être supprimé ; relancez la désinstallation.\r\n");
        goto done;
    }
    wchar_t summary[512];
    _snwprintf(summary, sizeof(summary) / sizeof(wchar_t),
               L"Désinstallation applicative terminée : %llu fichier(s) supprimé(s), %llu déjà absent(s).\r\n",
               (unsigned long long)removed, (unsigned long long)missing);
    post_log(summary);
    post_log(L".env, data, sauvegardes, journaux et volumes PostgreSQL sont conservés. Docker Desktop, Git et Visual Studio Code restent installés.\r\n");
    post_status(L"Désinstallation terminée — données conservées", 100);
    success = TRUE;

done:
    if (!success) post_status(L"Désinstallation interrompue — données conservées", 0);
    HeapFree(GetProcessHeap(), 0, options);
    PostMessageW(g_main, WM_HDP_FINISHED, success ? 1 : 0, 1);
    return 0;
}

static void update_uninstall_control(void) {
    if (!g_uninstall) return;
    wchar_t install_dir[MAX_PATH * 4];
    GetWindowTextW(g_path, install_dir,
                   (int)(sizeof(install_dir) / sizeof(wchar_t)));
    EnableWindow(g_uninstall, !g_installing && installation_path_is_safe(install_dir));
}

static void set_controls_installing(BOOL installing) {
    g_installing = installing;
    EnableWindow(g_path, !installing);
    EnableWindow(g_reliefweb, !installing);
    EnableWindow(g_github_token, !installing);
    EnableWindow(g_analyze, !installing);
    EnableWindow(g_install, !installing);
    EnableWindow(g_uninstall, FALSE);
    EnableWindow(g_open_folder, !installing);
    EnableWindow(g_r_module, !installing);
    EnableWindow(g_cancel, installing && !g_uninstalling);
    set_dependency_control(g_docker, L"Docker Desktop (requis)", g_docker_present, g_winget_present);
    set_dependency_control(g_git, L"Git (optionnel)", g_git_present, g_winget_present);
    set_dependency_control(g_vscode, L"Visual Studio Code (optionnel)", g_vscode_present, g_winget_present);
    if (!installing) update_uninstall_control();
}

static void begin_install(void) {
    if (g_installing) return;
    InstallOptions *options = HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, sizeof(InstallOptions));
    if (!options) return;
    GetWindowTextW(g_path, options->install_dir, (int)(sizeof(options->install_dir) / sizeof(wchar_t)));
    GetWindowTextW(g_reliefweb, options->reliefweb_appname, (int)(sizeof(options->reliefweb_appname) / sizeof(wchar_t)));
    GetWindowTextW(g_github_token, options->github_token, (int)(sizeof(options->github_token) / sizeof(wchar_t)));
    options->install_docker = SendMessageW(g_docker, BM_GETCHECK, 0, 0) == BST_CHECKED;
    options->install_git = SendMessageW(g_git, BM_GETCHECK, 0, 0) == BST_CHECKED;
    options->install_vscode = SendMessageW(g_vscode, BM_GETCHECK, 0, 0) == BST_CHECKED;
    options->install_r_module = SendMessageW(g_r_module, BM_GETCHECK, 0, 0) == BST_CHECKED;

    size_t path_length = wcslen(options->install_dir);
    while (path_length > 3 && (options->install_dir[path_length - 1] == L'\\' || options->install_dir[path_length - 1] == L'/')) {
        options->install_dir[--path_length] = 0;
    }
    if (path_length < 3 || !((iswalpha(options->install_dir[0]) && options->install_dir[1] == L':') ||
                             (options->install_dir[0] == L'\\' && options->install_dir[1] == L'\\'))) {
        MessageBoxW(g_main, L"Choisissez un chemin absolu Windows valide.", APP_NAME, MB_OK | MB_ICONWARNING);
        HeapFree(GetProcessHeap(), 0, options);
        return;
    }
    if (!appname_is_valid(options->reliefweb_appname)) {
        MessageBoxW(g_main, L"L'appname ReliefWeb ne peut contenir que lettres, chiffres, tirets, points et caractères de soulignement.", APP_NAME, MB_OK | MB_ICONWARNING);
        HeapFree(GetProcessHeap(), 0, options);
        return;
    }
    if (!secret_line_is_valid(options->github_token)) {
        MessageBoxW(g_main, L"Le jeton GitHub ne peut pas contenir de retour à la ligne.", APP_NAME, MB_OK | MB_ICONWARNING);
        HeapFree(GetProcessHeap(), 0, options);
        return;
    }
    if (!g_docker_present && !options->install_docker) {
        MessageBoxW(g_main, L"Docker Desktop est requis. Cochez explicitement sa case pour autoriser son installation.", APP_NAME, MB_OK | MB_ICONWARNING);
        HeapFree(GetProcessHeap(), 0, options);
        return;
    }
    if ((options->install_docker || options->install_git || options->install_vscode) && !g_winget_present) {
        int answer = MessageBoxW(g_main,
            L"winget est absent. Voulez-vous ouvrir la page officielle Microsoft App Installer ?",
            APP_NAME, MB_YESNO | MB_ICONINFORMATION);
        if (answer == IDYES) open_url(L"ms-windows-store://pdp/?ProductId=9NBLGGH4NNS1");
        HeapFree(GetProcessHeap(), 0, options);
        return;
    }

    refresh_docker_disk_free_space();
    if (g_docker_disk_free_bytes > 0 &&
        g_docker_disk_free_bytes < 5ULL * 1024ULL * 1024ULL * 1024ULL) {
        wchar_t disk_warning[640];
        unsigned long long free_mib = (unsigned long long)(g_docker_disk_free_bytes / (1024ULL * 1024ULL));
        _snwprintf(disk_warning, sizeof(disk_warning) / sizeof(wchar_t),
                   L"Il ne reste que %llu Mo sur le disque de LOCALAPPDATA, emplacement Docker par défaut. Les images et caches peuvent saturer le disque et bloquer Docker Desktop.\n\nLibérez idéalement au moins 10 Go. Voulez-vous néanmoins continuer ?",
                   free_mib);
        int disk_answer = MessageBoxW(g_main, disk_warning, APP_NAME,
                                      MB_YESNO | MB_ICONWARNING | MB_DEFBUTTON2);
        if (disk_answer != IDYES) {
            HeapFree(GetProcessHeap(), 0, options);
            return;
        }
    }

    wchar_t existing_env_path[MAX_PATH * 4];
    _snwprintf(existing_env_path, sizeof(existing_env_path) / sizeof(wchar_t),
               L"%ls\\.env", options->install_dir);
    BOOL is_upgrade = file_exists(existing_env_path);
    const wchar_t *confirmation_text;
    if (is_upgrade) {
        confirmation_text = options->install_r_module
            ? L"Une installation HDP existante a été détectée. La mise à niveau conservera .env, data et le volume PostgreSQL, puis activera aussi le module R. Une sauvegarde de .env sera créée. Continuer ?"
            : L"Une installation HDP existante a été détectée. La mise à niveau conservera .env, data et le volume PostgreSQL. Une sauvegarde de .env sera créée. Continuer ?";
    } else {
        confirmation_text = options->install_r_module
            ? L"L'application et le module analytique R seront installés. Le premier téléchargement de R dépasse 300 Mo et peut durer plusieurs minutes. Continuer ?"
            : L"Le cœur Python/PostGIS sera installé. Le module R restera différé et pourra être ajouté plus tard en relançant cet installateur. Continuer ?";
    }
    int confirmation = MessageBoxW(g_main,
        confirmation_text,
        APP_NAME, MB_YESNO | MB_ICONQUESTION);
    if (confirmation != IDYES) {
        HeapFree(GetProcessHeap(), 0, options);
        return;
    }

    append_log_control(is_upgrade
        ? L"\r\n--- Mise à niveau d'une installation existante ---\r\n"
        : L"\r\n--- Nouvelle installation ---\r\n");
    InterlockedExchange(&g_cancel_requested, 0);
    set_controls_installing(TRUE);
    wcsncpy(g_stage_status, L"Démarrage de l'installation", (sizeof(g_stage_status) / sizeof(wchar_t)) - 1);
    g_stage_status[(sizeof(g_stage_status) / sizeof(wchar_t)) - 1] = 0;
    g_stage_progress = 2;
    g_stage_started = GetTickCount64();
    SetTimer(g_main, ID_ACTIVITY_TIMER, 1000, NULL);
    SendMessageW(g_progress, PBM_SETPOS, 2, 0);
    HANDLE thread = CreateThread(NULL, 0, install_thread, options, 0, NULL);
    if (!thread) {
        KillTimer(g_main, ID_ACTIVITY_TIMER);
        set_controls_installing(FALSE);
        HeapFree(GetProcessHeap(), 0, options);
        MessageBoxW(g_main, L"Impossible de démarrer la tâche d'installation.", APP_NAME, MB_OK | MB_ICONERROR);
        return;
    }
    CloseHandle(thread);
}

static void begin_uninstall(void) {
    if (g_installing) return;
    InstallOptions *options = HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, sizeof(InstallOptions));
    if (!options) return;
    GetWindowTextW(g_path, options->install_dir,
                   (int)(sizeof(options->install_dir) / sizeof(wchar_t)));
    size_t length = wcslen(options->install_dir);
    while (length > 3 && (options->install_dir[length - 1] == L'\\' ||
                          options->install_dir[length - 1] == L'/')) {
        options->install_dir[--length] = 0;
    }
    if (!installation_path_is_safe(options->install_dir)) {
        MessageBoxW(g_main,
            L"Désinstallation refusée : ce dossier ne contient pas un marqueur HDP valide et les fichiers attendus. Relancez d'abord cet installateur pour mettre à niveau une ancienne installation.",
            APP_NAME, MB_OK | MB_ICONWARNING);
        HeapFree(GetProcessHeap(), 0, options);
        return;
    }
    int answer = MessageBoxW(
        g_main,
        L"Désinstaller les fichiers applicatifs HDP de ce dossier ?\n\n"
        L"Les services seront arrêtés et le raccourci Bureau sera supprimé seulement s'il cible cette installation.\n\n"
        L"Seront conservés : .env, data, sauvegardes, journaux et volumes PostgreSQL. Docker Desktop, Git et Visual Studio Code resteront installés.\n\n"
        L"Aucun volume Docker ne sera supprimé. Continuer ?",
        APP_NAME, MB_YESNO | MB_ICONWARNING | MB_DEFBUTTON2);
    if (answer != IDYES) {
        HeapFree(GetProcessHeap(), 0, options);
        return;
    }
    append_log_control(L"\r\n--- Désinstallation applicative non destructive ---\r\n");
    g_uninstalling = TRUE;
    InterlockedExchange(&g_cancel_requested, 0);
    set_controls_installing(TRUE);
    wcsncpy(g_stage_status, L"Démarrage de la désinstallation",
            (sizeof(g_stage_status) / sizeof(wchar_t)) - 1);
    g_stage_status[(sizeof(g_stage_status) / sizeof(wchar_t)) - 1] = 0;
    g_stage_progress = 5;
    g_stage_started = GetTickCount64();
    SetTimer(g_main, ID_ACTIVITY_TIMER, 1000, NULL);
    SendMessageW(g_progress, PBM_SETPOS, 5, 0);
    HANDLE thread = CreateThread(NULL, 0, uninstall_thread, options, 0, NULL);
    if (!thread) {
        KillTimer(g_main, ID_ACTIVITY_TIMER);
        g_uninstalling = FALSE;
        set_controls_installing(FALSE);
        HeapFree(GetProcessHeap(), 0, options);
        MessageBoxW(g_main, L"Impossible de démarrer la tâche de désinstallation.",
                    APP_NAME, MB_OK | MB_ICONERROR);
        return;
    }
    CloseHandle(thread);
}

static void layout_controls(int width, int height) {
    int margin = 22;
    int content_width = width - margin * 2;
    if (content_width < 400) content_width = 400;
    MoveWindow(g_path, margin + 150, 83, content_width - 150, 25, TRUE);
    MoveWindow(g_reliefweb, margin + 150, 119, content_width - 150, 25, TRUE);
    MoveWindow(g_github_token, margin + 150, 155, content_width - 150, 25, TRUE);
    MoveWindow(g_docker, margin, 212, content_width, 24, TRUE);
    MoveWindow(g_git, margin, 238, content_width, 24, TRUE);
    MoveWindow(g_vscode, margin, 264, content_width, 24, TRUE);
    MoveWindow(g_r_module, margin, 290, content_width, 24, TRUE);

    MoveWindow(g_analyze, margin, 332, 150, 30, TRUE);
    MoveWindow(g_install, margin + 160, 332, 205, 30, TRUE);
    MoveWindow(g_uninstall, margin + 375, 332, 190, 30, TRUE);
    MoveWindow(g_open_folder, margin, 370, 145, 30, TRUE);
    MoveWindow(g_open_log, margin + 155, 370, 120, 30, TRUE);
    MoveWindow(g_cancel, margin + 285, 370, 100, 30, TRUE);
    MoveWindow(g_progress, margin, 414, content_width, 18, TRUE);
    MoveWindow(g_status, margin, 439, content_width, 23, TRUE);
    int log_height = height - 508;
    if (log_height < 120) log_height = 120;
    MoveWindow(g_log, margin, 487, content_width, log_height, TRUE);
}

static HWND create_control(const wchar_t *class_name, const wchar_t *text, DWORD style,
                           int id, HWND parent) {
    HWND control = CreateWindowExW(0, class_name, text, WS_CHILD | WS_VISIBLE | style,
                                   0, 0, 0, 0, parent, (HMENU)(INT_PTR)id, g_instance, NULL);
    if (control && g_font) SendMessageW(control, WM_SETFONT, (WPARAM)g_font, TRUE);
    return control;
}

static LRESULT CALLBACK window_proc(HWND window, UINT message, WPARAM wparam, LPARAM lparam) {
    switch (message) {
        case WM_CREATE: {
            g_font = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
            HWND header = create_control(L"STATIC", L"Humanitarian Data Platform", SS_LEFT, 0, window);
            HWND subtitle = create_control(L"STATIC", L"Installateur Windows natif 6.0.0 — données humanitaires et sanitaires", SS_LEFT, 0, window);
            HWND path_label = create_control(L"STATIC", L"Dossier d'installation", SS_LEFT, 0, window);
            HWND relief_label = create_control(L"STATIC", L"Appname ReliefWeb", SS_LEFT, 0, window);
            HWND github_label = create_control(L"STATIC", L"Jeton GitHub", SS_LEFT, 0, window);
            HWND dep_label = create_control(L"STATIC", L"Logiciels tiers et module R — aucune case n'est cochée automatiquement", SS_LEFT, 0, window);
            HWND log_label = create_control(L"STATIC", L"Journal détaillé (défilement disponible)", SS_LEFT, 0, window);
            MoveWindow(header, 22, 18, 700, 28, TRUE);
            MoveWindow(subtitle, 22, 48, 760, 22, TRUE);
            MoveWindow(path_label, 22, 87, 145, 22, TRUE);
            MoveWindow(relief_label, 22, 123, 145, 22, TRUE);
            MoveWindow(github_label, 22, 159, 145, 22, TRUE);
            MoveWindow(dep_label, 22, 187, 700, 22, TRUE);
            MoveWindow(log_label, 22, 466, 500, 19, TRUE);

            g_path = create_control(L"EDIT", L"", WS_BORDER | ES_AUTOHSCROLL | WS_TABSTOP, ID_PATH, window);
            g_reliefweb = create_control(L"EDIT", L"", WS_BORDER | ES_AUTOHSCROLL | WS_TABSTOP, ID_RELIEFWEB, window);
            SendMessageW(g_reliefweb, EM_SETCUEBANNER, TRUE, (LPARAM)L"facultatif — identifiant pré-approuvé par ReliefWeb");
            g_github_token = create_control(L"EDIT", L"", WS_BORDER | ES_AUTOHSCROLL | ES_PASSWORD | WS_TABSTOP, ID_GITHUB_TOKEN, window);
            SendMessageW(g_github_token, EM_SETCUEBANNER, TRUE, (LPARAM)L"facultatif — conservé dans .env, jamais affiché dans le journal");
            g_docker = create_control(L"BUTTON", L"Docker Desktop (analyse en cours)", BS_AUTOCHECKBOX | WS_TABSTOP, ID_DOCKER, window);
            g_git = create_control(L"BUTTON", L"Git (analyse en cours)", BS_AUTOCHECKBOX | WS_TABSTOP, ID_GIT, window);
            g_vscode = create_control(L"BUTTON", L"Visual Studio Code (analyse en cours)", BS_AUTOCHECKBOX | WS_TABSTOP, ID_VSCODE, window);
            g_r_module = create_control(L"BUTTON", L"Module analytique R (optionnel, téléchargement supérieur à 300 Mo)", BS_AUTOCHECKBOX | WS_TABSTOP, ID_R_MODULE, window);
            SendMessageW(g_r_module, BM_SETCHECK, BST_UNCHECKED, 0);
            g_analyze = create_control(L"BUTTON", L"Analyser à nouveau", BS_PUSHBUTTON | WS_TABSTOP, ID_ANALYZE, window);
            g_install = create_control(L"BUTTON", L"Installer / mettre à niveau", BS_DEFPUSHBUTTON | WS_TABSTOP, ID_INSTALL, window);
            g_uninstall = create_control(L"BUTTON", L"Désinstaller HDP", BS_PUSHBUTTON | WS_TABSTOP, ID_UNINSTALL, window);
            EnableWindow(g_uninstall, FALSE);
            g_open_folder = create_control(L"BUTTON", L"Ouvrir le dossier", BS_PUSHBUTTON | WS_TABSTOP, ID_OPEN_FOLDER, window);
            g_open_log = create_control(L"BUTTON", L"Ouvrir le journal", BS_PUSHBUTTON | WS_TABSTOP, ID_OPEN_LOG, window);
            g_cancel = create_control(L"BUTTON", L"Annuler", BS_PUSHBUTTON | WS_TABSTOP, ID_CANCEL, window);
            EnableWindow(g_cancel, FALSE);
            g_progress = create_control(PROGRESS_CLASSW, L"", PBS_SMOOTH, ID_PROGRESS, window);
            SendMessageW(g_progress, PBM_SETRANGE, 0, MAKELPARAM(0, 100));
            g_status = create_control(L"STATIC", L"Prêt pour l'analyse de l'environnement.", SS_LEFT, ID_STATUS, window);
            g_log = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", L"",
                                    WS_CHILD | WS_VISIBLE | WS_TABSTOP | WS_VSCROLL |
                                    ES_MULTILINE | ES_READONLY | ES_AUTOVSCROLL | ES_NOHIDESEL,
                                    0, 0, 0, 0, window, (HMENU)(INT_PTR)ID_LOG, g_instance, NULL);
            SendMessageW(g_log, WM_SETFONT, (WPARAM)g_font, TRUE);
            SendMessageW(g_log, EM_SETLIMITTEXT, 4 * 1024 * 1024, 0);

            wchar_t user_profile[MAX_PATH * 2] = L"C:\\";
            GetEnvironmentVariableW(L"USERPROFILE", user_profile, (DWORD)(sizeof(user_profile) / sizeof(wchar_t)));
            wchar_t default_path[MAX_PATH * 4];
            _snwprintf(default_path, sizeof(default_path) / sizeof(wchar_t), L"%ls\\HumanitarianDataPlatform", user_profile);
            SetWindowTextW(g_path, default_path);
            append_log_control(L"Interface native chargée. L'installation restera en tâche de fond et cette fenêtre restera utilisable.\r\n");
            PostMessageW(window, WM_HDP_ANALYZE, 0, 0);
            return 0;
        }
        case WM_SIZE:
            layout_controls(LOWORD(lparam), HIWORD(lparam));
            return 0;
        case WM_GETMINMAXINFO: {
            MINMAXINFO *info = (MINMAXINFO *)lparam;
            info->ptMinTrackSize.x = 820;
            info->ptMinTrackSize.y = 730;
            return 0;
        }
        case WM_COMMAND:
            switch (LOWORD(wparam)) {
                case ID_PATH:
                    if (HIWORD(wparam) == EN_CHANGE) update_uninstall_control();
                    return 0;
                case ID_ANALYZE:
                    analyze_system();
                    return 0;
                case ID_INSTALL:
                    begin_install();
                    return 0;
                case ID_UNINSTALL:
                    begin_uninstall();
                    return 0;
                case ID_OPEN_FOLDER: {
                    wchar_t path[MAX_PATH * 4];
                    GetWindowTextW(g_path, path, (int)(sizeof(path) / sizeof(wchar_t)));
                    if (directory_exists(path)) ShellExecuteW(NULL, L"open", path, NULL, NULL, SW_SHOWNORMAL);
                    else MessageBoxW(window, L"Le dossier n'existe pas encore.", APP_NAME, MB_OK | MB_ICONINFORMATION);
                    return 0;
                }
                case ID_OPEN_LOG:
                    ShellExecuteW(NULL, L"open", g_log_path, NULL, NULL, SW_SHOWNORMAL);
                    return 0;
                case ID_CANCEL:
                    if (g_installing && !cancel_requested()) {
                        InterlockedExchange(&g_cancel_requested, 1);
                        EnableWindow(g_cancel, FALSE);
                        append_log_control(L"Annulation demandée : arrêt contrôlé de la commande en cours…\r\n");
                        SetWindowTextW(g_status, L"Annulation en cours — conservation des données");
                    }
                    return 0;
            }
            break;
        case WM_HDP_ANALYZE:
            analyze_system();
            return 0;
        case WM_HDP_DOCKER_ACTION:
            MessageBoxW(window,
                L"Docker Desktop vient d'être ouvert.\n\n"
                L"Lors du premier démarrage, Docker exige que vous lisiez et acceptiez ses propres conditions avant de lancer le moteur. Terminez l'écran affiché par Docker si cette confirmation apparaît.\n\n"
                L"L'installateur HDP poursuivra automatiquement dès que le moteur répondra. Il n'accepte aucun accord à votre place.",
                L"Action éventuellement requise dans Docker Desktop",
                MB_OK | MB_ICONINFORMATION | MB_SETFOREGROUND);
            return 0;
        case WM_HDP_LOG: {
            wchar_t *text = (wchar_t *)lparam;
            if (text) {
                append_log_control_ex(text, wparam == 0);
                HeapFree(GetProcessHeap(), 0, text);
            }
            return 0;
        }
        case WM_HDP_STATUS: {
            wchar_t *text = (wchar_t *)lparam;
            if (text) {
                wcsncpy(g_stage_status, text, (sizeof(g_stage_status) / sizeof(wchar_t)) - 1);
                g_stage_status[(sizeof(g_stage_status) / sizeof(wchar_t)) - 1] = 0;
                SetWindowTextW(g_status, text);
                HeapFree(GetProcessHeap(), 0, text);
            }
            int progress = (int)wparam;
            if (progress >= 0 && progress <= 100) {
                g_stage_progress = progress;
                SendMessageW(g_progress, PBM_SETPOS, progress, 0);
            }
            g_stage_started = GetTickCount64();
            return 0;
        }
        case WM_TIMER:
            if (wparam == ID_ACTIVITY_TIMER && g_installing) {
                ULONGLONG elapsed = (GetTickCount64() - g_stage_started) / 1000;
                DWORD minutes = (DWORD)(elapsed / 60);
                DWORD seconds = (DWORD)(elapsed % 60);
                wchar_t activity[640];
                _snwprintf(activity, sizeof(activity) / sizeof(wchar_t),
                           L"%ls — activité depuis %02lu:%02lu", g_stage_status, minutes, seconds);
                SetWindowTextW(g_status, activity);
                if (g_stage_progress > 0 && g_stage_progress < 100) {
                    int offset = (int)(elapsed / 5);
                    if (offset > 4) offset = 4;
                    int animated = g_stage_progress + offset;
                    if (animated > 98) animated = 98;
                    SendMessageW(g_progress, PBM_SETPOS, animated, 0);
                }
            }
            return 0;
        case WM_HDP_FINISHED:
            KillTimer(g_main, ID_ACTIVITY_TIMER);
            {
            BOOL was_uninstall = lparam == 1;
            g_uninstalling = FALSE;
            set_controls_installing(FALSE);
            analyze_system();
            if (wparam) {
                MessageBoxW(window, was_uninstall
                    ? L"Désinstallation applicative terminée. Les données, configurations, sauvegardes, journaux et volumes PostgreSQL ont été conservés."
                    : L"Installation terminée. L'interface a été ouverte dans votre navigateur.\n\nLe journal reste disponible dans cette fenêtre.",
                    APP_NAME, MB_OK | MB_ICONINFORMATION);
            } else {
                MessageBoxW(window, was_uninstall
                    ? L"La désinstallation n'est pas terminée. Les données ont été conservées ; consultez le journal avant de réessayer."
                    : L"L'installation n'est pas terminée. Consultez le journal affiché et utilisez le bouton « Ouvrir le journal » pour transmettre le diagnostic.",
                    APP_NAME, MB_OK | MB_ICONERROR);
            }
            }
            return 0;
        case WM_CLOSE:
            if (g_installing) {
                if (g_uninstalling) {
                    MessageBoxW(window,
                        L"La désinstallation contrôlée est en cours. Attendez sa fin afin de ne pas laisser un état partiel.",
                        APP_NAME, MB_OK | MB_ICONWARNING);
                    return 0;
                }
                int answer = MessageBoxW(
                    window,
                    L"Une installation est en cours. Voulez-vous demander son annulation contrôlée ?\n\nLes données et volumes existants seront conservés.",
                    APP_NAME, MB_YESNO | MB_ICONWARNING | MB_DEFBUTTON2);
                if (answer == IDYES && !cancel_requested()) {
                    InterlockedExchange(&g_cancel_requested, 1);
                    EnableWindow(g_cancel, FALSE);
                    append_log_control(L"Annulation demandée depuis la fermeture de la fenêtre…\r\n");
                }
                return 0;
            }
            DestroyWindow(window);
            return 0;
        case WM_DESTROY:
            if (g_winsock_initialized) {
                WSACleanup();
                g_winsock_initialized = FALSE;
            }
            PostQuitMessage(0);
            return 0;
    }
    return DefWindowProcW(window, message, wparam, lparam);
}

static void initialize_log_path(void) {
    wchar_t local_appdata[MAX_PATH * 2] = L".";
    GetEnvironmentVariableW(L"LOCALAPPDATA", local_appdata, (DWORD)(sizeof(local_appdata) / sizeof(wchar_t)));
    wchar_t log_dir[MAX_PATH * 4];
    _snwprintf(log_dir, sizeof(log_dir) / sizeof(wchar_t), L"%ls\\HumanitarianDataPlatform\\logs", local_appdata);
    ensure_directory(log_dir);
    SYSTEMTIME now;
    GetLocalTime(&now);
    _snwprintf(g_log_path, sizeof(g_log_path) / sizeof(wchar_t),
               L"%ls\\installer-%04u%02u%02u-%02u%02u%02u.log", log_dir,
               now.wYear, now.wMonth, now.wDay, now.wHour, now.wMinute, now.wSecond);
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR command_line, int show_command) {
    (void)previous;
    (void)command_line;
    g_instance = instance;
    initialize_log_path();

    INITCOMMONCONTROLSEX controls = { sizeof(INITCOMMONCONTROLSEX), ICC_PROGRESS_CLASS | ICC_STANDARD_CLASSES };
    InitCommonControlsEx(&controls);

    WNDCLASSEXW window_class;
    ZeroMemory(&window_class, sizeof(window_class));
    window_class.cbSize = sizeof(window_class);
    window_class.lpfnWndProc = window_proc;
    window_class.hInstance = instance;
    window_class.hCursor = LoadCursorW(NULL, IDC_ARROW);
    window_class.hIcon = LoadIconW(NULL, IDI_APPLICATION);
    window_class.hIconSm = LoadIconW(NULL, IDI_APPLICATION);
    window_class.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    window_class.lpszClassName = MAIN_CLASS;
    if (!RegisterClassExW(&window_class)) return 1;

    wchar_t title[256];
    _snwprintf(title, sizeof(title) / sizeof(wchar_t), L"%ls — Installateur %ls", APP_NAME, APP_VERSION);
    g_main = CreateWindowExW(0, MAIN_CLASS, title,
                             WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN,
                             CW_USEDEFAULT, CW_USEDEFAULT, 980, 830,
                             NULL, NULL, instance, NULL);
    if (!g_main) return 2;
    ShowWindow(g_main, show_command);
    UpdateWindow(g_main);

    MSG message;
    while (GetMessageW(&message, NULL, 0, 0) > 0) {
        if (!IsDialogMessageW(g_main, &message)) {
            TranslateMessage(&message);
            DispatchMessageW(&message);
        }
    }
    return (int)message.wParam;
}

int WINAPI WinMain(HINSTANCE instance, HINSTANCE previous, LPSTR command_line, int show_command) {
    (void)command_line;
    return wWinMain(instance, previous, GetCommandLineW(), show_command);
}
