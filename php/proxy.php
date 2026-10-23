<?php
/**
 * On-demand PHP proxy for the german-word-splitter service.
 *
 * Starts the service if it is not reachable, then forwards the incoming
 * request (method, path, query, headers, body) and relays the reply.
 *
 * Configuration via environment variables (or edit the defaults below):
 *   GERMAN_WORD_SPLITTER_BIN     path to the executable
 *   GERMAN_WORD_SPLITTER_PORT    TCP port (default 8000)
 *   GERMAN_WORD_SPLITTER_SOCKET  Unix socket path; if set, used instead of TCP
 *   GERMAN_WORD_SPLITTER_LOG     log file of the launched service
 *
 * The upstream path is taken from PATH_INFO (e.g. proxy.php/split) or, if
 * absent, from the "path" query parameter (proxy.php?path=/split).
 * Requires the PHP curl extension and a POSIX-like system.
 */

$bin    = getenv('GERMAN_WORD_SPLITTER_BIN') ?: __DIR__ . '/../venv/bin/german-word-splitter';
$port   = (int)(getenv('GERMAN_WORD_SPLITTER_PORT') ?: 8000);
$socket = getenv('GERMAN_WORD_SPLITTER_SOCKET') ?: '';
$log    = getenv('GERMAN_WORD_SPLITTER_LOG') ?: '/dev/null';
$startupTimeout = 60; // seconds; the dictionary load can be slow

function fail(int $code, string $msg): void
{
    http_response_code($code);
    header('Content-Type: application/json');
    echo json_encode(['detail' => $msg]);
    exit;
}

function serviceUp(string $socket, int $port): bool
{
    $addr = $socket !== '' ? 'unix://' . $socket : "tcp://127.0.0.1:$port";
    $fp = @stream_socket_client($addr, $errno, $errstr, 1);
    if ($fp === false) {
        return false;
    }
    fclose($fp);
    return true;
}

function launch(string $bin, string $port, string $socket, string $log): void
{
    if (!is_executable($bin)) {
        fail(502, 'Service executable not found or not executable.');
    }
    $lock = fopen(sys_get_temp_dir() . '/german-word-splitter-' . md5($bin) . '.lock', 'c');
    flock($lock, LOCK_EX); // serialize concurrent launches
    if (!serviceUp($socket, (int)$port)) {
        $env = 'GERMAN_WORD_SPLITTER_PORT=' . escapeshellarg($port);
        if ($socket !== '') {
            $env .= ' GERMAN_WORD_SPLITTER_SOCKET=' . escapeshellarg($socket);
        }
        exec("env $env nohup " . escapeshellarg($bin)
            . ' >>' . escapeshellarg($log) . ' 2>&1 </dev/null &');
    }
    flock($lock, LOCK_UN);
    fclose($lock);
}

if (!serviceUp($socket, $port)) {
    launch($bin, (string)$port, $socket, $log);
    $deadline = time() + $startupTimeout;
    while (!serviceUp($socket, $port)) {
        if (time() > $deadline) {
            fail(504, 'Service did not start in time.');
        }
        usleep(200000);
    }
}

// The service is up; lift the execution limit so startup time doesn't count.
// The upstream request is still bounded by CURLOPT_TIMEOUT.
set_time_limit(0);

$path = $_SERVER['PATH_INFO'] ?? ($_GET['path'] ?? '/');
$path = '/' . ltrim($path, '/');
$query = $_GET;
unset($query['path']);
$qs = http_build_query($query);

$ch = curl_init();
if ($socket !== '') {
    curl_setopt($ch, CURLOPT_UNIX_SOCKET_PATH, $socket);
    $url = 'http://localhost' . $path;
} else {
    $url = "http://127.0.0.1:$port" . $path;
}
if ($qs !== '') {
    $url .= '?' . $qs;
}

$reqHeaders = [];
foreach (getallheaders() as $name => $value) {
    $lname = strtolower($name);
    if (in_array($lname, ['host', 'connection', 'content-length', 'transfer-encoding', 'accept-encoding'], true)) {
        continue;
    }
    $reqHeaders[] = "$name: $value";
}

$respHeaders = [];
curl_setopt_array($ch, [
    CURLOPT_URL            => $url,
    CURLOPT_CUSTOMREQUEST  => $_SERVER['REQUEST_METHOD'],
    CURLOPT_HTTPHEADER     => $reqHeaders,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT        => 60,
    CURLOPT_HEADERFUNCTION => function ($ch, $line) use (&$respHeaders) {
        $respHeaders[] = rtrim($line);
        return strlen($line);
    },
]);
$body = file_get_contents('php://input');
if ($body !== '' && $body !== false) {
    curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
}

$result = curl_exec($ch);
if ($result === false) {
    fail(502, 'Upstream error: ' . curl_error($ch));
}
http_response_code(curl_getinfo($ch, CURLINFO_RESPONSE_CODE));
curl_close($ch);

foreach ($respHeaders as $h) {
    $lh = strtolower($h);
    if ($h === '' || str_starts_with($lh, 'http/')
        || str_starts_with($lh, 'transfer-encoding:')
        || str_starts_with($lh, 'connection:')
        || str_starts_with($lh, 'content-length:')) {
        continue;
    }
    header($h, false);
}
echo $result;
