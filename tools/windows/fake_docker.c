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

static void trace_command(int argc, wchar_t **argv) {
    wchar_t temp[MAX_PATH * 4] = L".";
    GetEnvironmentVariableW(L"RUNNER_TEMP", temp, (DWORD)(sizeof(temp) / sizeof(wchar_t)));
    wchar_t path[MAX_PATH * 4];
    _snwprintf(path, sizeof(path) / sizeof(wchar_t), L"%ls\\hdp-fake-docker.log", temp);
    FILE *file = _wfopen(path, L"a, ccs=UTF-8");
    if (!file) return;
    for (int i = 0; i < argc; i++) fwprintf(file, L"%ls%ls", i ? L" | " : L"", argv[i]);
    fwprintf(file, L"\n");
    fclose(file);
}

static unsigned short read_port_from_env(const wchar_t *compose_path) {
    wchar_t directory[MAX_PATH * 4];
    wcsncpy(directory, compose_path, (sizeof(directory) / sizeof(wchar_t)) - 1);
    directory[(sizeof(directory) / sizeof(wchar_t)) - 1] = 0;
    wchar_t *slash = wcsrchr(directory, L'\\');
    if (!slash) slash = wcsrchr(directory, L'/');
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

static void serve_client(SOCKET client) {
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

static SOCKET bind_ipv4(unsigned short port) {
    SOCKET server = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (server == INVALID_SOCKET) return INVALID_SOCKET;
    BOOL exclusive = TRUE;
    setsockopt(server, SOL_SOCKET, SO_EXCLUSIVEADDRUSE, (const char *)&exclusive, sizeof(exclusive));
    struct sockaddr_in address;
    ZeroMemory(&address, sizeof(address));
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    address.sin_port = htons(port);
    if (bind(server, (struct sockaddr *)&address, sizeof(address)) != 0 || listen(server, 16) != 0) {
        closesocket(server);
        return INVALID_SOCKET;
    }
    return server;
}

static SOCKET bind_ipv6(unsigned short port) {
    SOCKET server = socket(AF_INET6, SOCK_STREAM, IPPROTO_TCP);
    if (server == INVALID_SOCKET) return INVALID_SOCKET;
    BOOL exclusive = TRUE;
    DWORD v6only = 1;
    setsockopt(server, SOL_SOCKET, SO_EXCLUSIVEADDRUSE, (const char *)&exclusive, sizeof(exclusive));
    setsockopt(server, IPPROTO_IPV6, IPV6_V6ONLY, (const char *)&v6only, sizeof(v6only));
    struct sockaddr_in6 address;
    ZeroMemory(&address, sizeof(address));
    address.sin6_family = AF_INET6;
    address.sin6_addr = in6addr_loopback;
    address.sin6_port = htons(port);
    if (bind(server, (struct sockaddr *)&address, sizeof(address)) != 0 || listen(server, 16) != 0) {
        closesocket(server);
        return INVALID_SOCKET;
    }
    return server;
}

static int health_server(unsigned short port) {
    WSADATA data;
    if (WSAStartup(MAKEWORD(2, 2), &data) != 0) return 21;
    SOCKET ipv4 = bind_ipv4(port);
    SOCKET ipv6 = bind_ipv6(port);
    if (ipv4 == INVALID_SOCKET && ipv6 == INVALID_SOCKET) return 23;
    for (;;) {
        fd_set reads;
        FD_ZERO(&reads);
        if (ipv4 != INVALID_SOCKET) FD_SET(ipv4, &reads);
        if (ipv6 != INVALID_SOCKET) FD_SET(ipv6, &reads);
        if (select(0, &reads, NULL, NULL, NULL) == SOCKET_ERROR) continue;
        if (ipv4 != INVALID_SOCKET && FD_ISSET(ipv4, &reads)) {
            SOCKET client = accept(ipv4, NULL, NULL);
            if (client != INVALID_SOCKET) serve_client(client);
        }
        if (ipv6 != INVALID_SOCKET && FD_ISSET(ipv6, &reads)) {
            SOCKET client = accept(ipv6, NULL, NULL);
            if (client != INVALID_SOCKET) serve_client(client);
        }
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
    Sleep(500);
    return 0;
}

int wmain(int argc, wchar_t **argv) {
    trace_command(argc, argv);
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
