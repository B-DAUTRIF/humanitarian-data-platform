#define _CRT_SECURE_NO_WARNINGS
#define UNICODE
#define _UNICODE
#define WIN32_LEAN_AND_MEAN

#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <wchar.h>

static unsigned short read_port_from_env(const wchar_t *compose_path) {
    wchar_t directory[MAX_PATH * 4];
    wcsncpy(directory, compose_path, (sizeof(directory) / sizeof(wchar_t)) - 1);
    directory[(sizeof(directory) / sizeof(wchar_t)) - 1] = 0;
    wchar_t *slash = wcsrchr(directory, L'\\');
    if (!slash) return 0;
    *slash = 0;
    wchar_t env_path[MAX_PATH * 4];
    _snwprintf(env_path, sizeof(env_path) / sizeof(wchar_t), L"%ls\\.env", directory);
    FILE *file = _wfopen(env_path, L"rb");
    if (!file) return 0;
    char line[4096];
    unsigned long port = 0;
    while (fgets(line, sizeof(line), file)) {
        if (sscanf(line, "HDP_PORT=%lu", &port) == 1) break;
    }
    fclose(file);
    if (port < 1024 || port > 65535) return 0;
    return (unsigned short)port;
}

static int health_server(unsigned short port) {
    WSADATA data;
    if (WSAStartup(MAKEWORD(2, 2), &data) != 0) return 21;
    SOCKET server = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (server == INVALID_SOCKET) return 22;
    struct sockaddr_in address;
    ZeroMemory(&address, sizeof(address));
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    address.sin_port = htons(port);
    if (bind(server, (struct sockaddr *)&address, sizeof(address)) != 0) return 23;
    if (listen(server, 16) != 0) return 24;
    for (;;) {
        SOCKET client = accept(server, NULL, NULL);
        if (client == INVALID_SOCKET) continue;
        char request[2048];
        recv(client, request, sizeof(request), 0);
        const char body[] = "{\"name\":\"Humanitarian Data Platform\",\"status\":\"ok\"}";
        char response[4096];
        int length = _snprintf(response, sizeof(response),
            "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: %u\r\nConnection: close\r\n\r\n%s",
            (unsigned)strlen(body), body);
        send(client, response, length, 0);
        closesocket(client);
    }
}

static int spawn_health_server(unsigned short port) {
    wchar_t executable[MAX_PATH * 4];
    if (!GetModuleFileNameW(NULL, executable, (DWORD)(sizeof(executable) / sizeof(wchar_t)))) return 31;
    wchar_t command[MAX_PATH * 5];
    _snwprintf(command, sizeof(command) / sizeof(wchar_t), L"\"%ls\" --health-server %u", executable, port);
    STARTUPINFOW startup;
    PROCESS_INFORMATION process;
    ZeroMemory(&startup, sizeof(startup));
    startup.cb = sizeof(startup);
    ZeroMemory(&process, sizeof(process));
    BOOL ok = CreateProcessW(NULL, command, NULL, NULL, FALSE,
                             CREATE_NO_WINDOW | DETACHED_PROCESS,
                             NULL, NULL, &startup, &process);
    if (!ok) return 32;
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    Sleep(300);
    return 0;
}

int wmain(int argc, wchar_t **argv) {
    if (argc >= 3 && !_wcsicmp(argv[1], L"--health-server")) {
        unsigned long port = wcstoul(argv[2], NULL, 10);
        return health_server((unsigned short)port);
    }
    if (argc >= 2 && !_wcsicmp(argv[1], L"version")) {
        wprintf(L"27.0.0\n");
        return 0;
    }
    if (argc >= 3 && !_wcsicmp(argv[1], L"desktop") && !_wcsicmp(argv[2], L"start")) return 0;

    const wchar_t *compose_path = NULL;
    int up = 0;
    for (int i = 1; i < argc; i++) {
        if (!_wcsicmp(argv[i], L"-f") && i + 1 < argc) compose_path = argv[++i];
        else if (!_wcsicmp(argv[i], L"up")) up = 1;
    }
    if (up) {
        if (!compose_path) return 41;
        unsigned short port = read_port_from_env(compose_path);
        if (!port) return 42;
        return spawn_health_server(port);
    }
    return 0;
}
