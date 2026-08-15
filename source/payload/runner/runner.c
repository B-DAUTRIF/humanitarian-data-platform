#define _POSIX_C_SOURCE 200809L

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define PATH_BUFFER 4096
#define TEXT_BUFFER 128

static const char *required_env(const char *name) {
    const char *value = getenv(name);
    if (value == NULL || value[0] == '\0') {
        fprintf(stderr, "Variable requise absente: %s\n", name);
        exit(2);
    }
    return value;
}

static bool valid_job_id(const char *value) {
    if (strlen(value) != 36U) return false;
    for (size_t index = 0; value[index] != '\0'; ++index) {
        const char c = value[index];
        if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || c == '-')) return false;
    }
    return true;
}

static void make_directory(const char *path) {
    if (mkdir(path, 0777) != 0 && errno != EEXIST) {
        fprintf(stderr, "mkdir %s: %s\n", path, strerror(errno));
    }
}

static void write_text(const char *directory, const char *name, const char *value) {
    char path[PATH_BUFFER];
    if (snprintf(path, sizeof(path), "%s/%s", directory, name) >= (int)sizeof(path)) return;
    const int descriptor = open(path, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0644);
    if (descriptor < 0) return;
    const size_t length = strlen(value);
    size_t written = 0;
    while (written < length) {
        const ssize_t count = write(descriptor, value + written, length - written);
        if (count <= 0) break;
        written += (size_t)count;
    }
    (void)close(descriptor);
}

static long read_bounded_integer(const char *directory, const char *name, long minimum, long maximum) {
    char path[PATH_BUFFER];
    char buffer[TEXT_BUFFER] = {0};
    if (snprintf(path, sizeof(path), "%s/%s", directory, name) >= (int)sizeof(path)) return -1;
    const int descriptor = open(path, O_RDONLY | O_CLOEXEC);
    if (descriptor < 0) return -1;
    const ssize_t count = read(descriptor, buffer, sizeof(buffer) - 1U);
    (void)close(descriptor);
    if (count <= 0) return -1;
    char *end = NULL;
    errno = 0;
    const long value = strtol(buffer, &end, 10);
    if (errno != 0 || end == buffer || value < minimum || value > maximum) return -1;
    return value;
}

static void utc_now(char *buffer, size_t size) {
    const time_t current = time(NULL);
    struct tm value;
    if (gmtime_r(&current, &value) == NULL) {
        snprintf(buffer, size, "1970-01-01T00:00:00Z");
        return;
    }
    (void)strftime(buffer, size, "%Y-%m-%dT%H:%M:%SZ", &value);
}

static void set_limit(int resource, rlim_t value) {
    const struct rlimit limit = {.rlim_cur = value, .rlim_max = value};
    (void)setrlimit(resource, &limit);
}

static void run_child(
    const char *directory,
    const char *language,
    const char *command,
    long timeout_seconds,
    long max_output_bytes
) {
    char stdout_path[PATH_BUFFER];
    char stderr_path[PATH_BUFFER];
    if (snprintf(stdout_path, sizeof(stdout_path), "%s/stdout.txt", directory) >= (int)sizeof(stdout_path)) _exit(125);
    if (snprintf(stderr_path, sizeof(stderr_path), "%s/stderr.txt", directory) >= (int)sizeof(stderr_path)) _exit(125);
    const int output = open(stdout_path, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    const int errors = open(stderr_path, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (output < 0 || errors < 0) _exit(125);
    if (dup2(output, STDOUT_FILENO) < 0 || dup2(errors, STDERR_FILENO) < 0) _exit(125);
    (void)close(output);
    (void)close(errors);
    if (chdir(directory) != 0) _exit(125);

    set_limit(RLIMIT_CORE, 0);
    set_limit(RLIMIT_CPU, (rlim_t)(timeout_seconds + 1));
    set_limit(RLIMIT_FSIZE, (rlim_t)max_output_bytes);
    set_limit(RLIMIT_NOFILE, 64);
    set_limit(RLIMIT_NPROC, 32);
    alarm((unsigned int)timeout_seconds);

    char *const safe_environment[] = {
        "HOME=/tmp",
        "TMPDIR=/tmp",
        "LANG=C.UTF-8",
        "LC_ALL=C.UTF-8",
        "PYTHONNOUSERSITE=1",
        "PYTHONDONTWRITEBYTECODE=1",
        "R_ENVIRON_USER=/dev/null",
        "R_PROFILE_USER=/dev/null",
        NULL,
    };
    if (strcmp(language, "python") == 0) {
        char *const arguments[] = {(char *)command, "-I", "-B", "script.py", NULL};
        execve(command, arguments, safe_environment);
    } else {
        char *const arguments[] = {(char *)command, "--vanilla", "script.R", NULL};
        execve(command, arguments, safe_environment);
    }
    dprintf(STDERR_FILENO, "Impossible de lancer le moteur %s: %s\n", language, strerror(errno));
    _exit(126);
}

static void process_job(
    const char *spool,
    const char *language,
    const char *command,
    const char *job_id
) {
    char pending[PATH_BUFFER];
    char running[PATH_BUFFER];
    char completed[PATH_BUFFER];
    if (snprintf(pending, sizeof(pending), "%s/pending/%s/%s", spool, language, job_id) >= (int)sizeof(pending)) return;
    if (snprintf(running, sizeof(running), "%s/running/%s/%s", spool, language, job_id) >= (int)sizeof(running)) return;
    if (snprintf(completed, sizeof(completed), "%s/completed/%s/%s", spool, language, job_id) >= (int)sizeof(completed)) return;
    if (rename(pending, running) != 0) return;

    const long timeout_seconds = read_bounded_integer(running, "timeout_seconds", 1, 300);
    const long max_output_bytes = read_bounded_integer(running, "max_output_bytes", 1024, 1048576);
    if (timeout_seconds < 0 || max_output_bytes < 0) {
        write_text(running, "status.txt", "failed");
        write_text(running, "stderr.txt", "Paramètres d'exécution invalides.\n");
        write_text(running, "exit_code.txt", "125");
        (void)rename(running, completed);
        return;
    }

    char timestamp[64];
    utc_now(timestamp, sizeof(timestamp));
    write_text(running, "started_at.txt", timestamp);
    write_text(running, "status.txt", "running");
    const time_t started = time(NULL);
    const pid_t child = fork();
    if (child == 0) run_child(running, language, command, timeout_seconds, max_output_bytes);
    if (child < 0) {
        write_text(running, "status.txt", "failed");
        write_text(running, "stderr.txt", "Impossible de créer le processus isolé.\n");
        write_text(running, "exit_code.txt", "125");
        (void)rename(running, completed);
        return;
    }

    int wait_status = 0;
    bool timed_out = false;
    while (waitpid(child, &wait_status, WNOHANG) == 0) {
        if (difftime(time(NULL), started) > (double)timeout_seconds + 1.0) {
            timed_out = true;
            (void)kill(child, SIGKILL);
            (void)waitpid(child, &wait_status, 0);
            break;
        }
        struct timespec pause = {.tv_sec = 0, .tv_nsec = 100000000L};
        (void)nanosleep(&pause, NULL);
    }

    char code[32];
    int exit_code = -1;
    const char *status = "failed";
    if (timed_out || (WIFSIGNALED(wait_status) && WTERMSIG(wait_status) == SIGALRM)) {
        status = "timed_out";
    } else if (WIFEXITED(wait_status)) {
        exit_code = WEXITSTATUS(wait_status);
        status = exit_code == 0 ? "completed" : "failed";
    }
    snprintf(code, sizeof(code), "%d", exit_code);
    write_text(running, "exit_code.txt", code);
    write_text(running, "status.txt", status);
    utc_now(timestamp, sizeof(timestamp));
    write_text(running, "finished_at.txt", timestamp);
    (void)rename(running, completed);
}

static void write_heartbeat(const char *spool, const char *language) {
    char directory[PATH_BUFFER];
    char timestamp[64];
    if (snprintf(directory, sizeof(directory), "%s/heartbeat", spool) >= (int)sizeof(directory)) return;
    make_directory(directory);
    utc_now(timestamp, sizeof(timestamp));
    write_text(directory, language, timestamp);
    char source[PATH_BUFFER];
    char target[PATH_BUFFER];
    if (snprintf(source, sizeof(source), "%s/%s", directory, language) >= (int)sizeof(source)) return;
    if (snprintf(target, sizeof(target), "%s/%s.txt", directory, language) >= (int)sizeof(target)) return;
    (void)rename(source, target);
}

int main(void) {
    const char *spool = required_env("HDP_SPOOL");
    const char *language = required_env("HDP_RUNNER_LANGUAGE");
    const char *command = required_env("HDP_RUNNER_COMMAND");
    if (strcmp(language, "python") != 0 && strcmp(language, "r") != 0) {
        fprintf(stderr, "Langage runner invalide\n");
        return 2;
    }
    char pending[PATH_BUFFER];
    if (snprintf(pending, sizeof(pending), "%s/pending/%s", spool, language) >= (int)sizeof(pending)) return 2;
    for (;;) {
        write_heartbeat(spool, language);
        DIR *directory = opendir(pending);
        if (directory != NULL) {
            struct dirent *entry = NULL;
            while ((entry = readdir(directory)) != NULL) {
                if (entry->d_name[0] == '.' || !valid_job_id(entry->d_name)) continue;
                process_job(spool, language, command, entry->d_name);
            }
            (void)closedir(directory);
        }
        sleep(1);
    }
}
