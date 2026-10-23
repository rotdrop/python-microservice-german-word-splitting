<?php
/**
 * Merge the per-request coverage files into a single Clover XML report.
 *
 * Usage: php tests/php/merge_coverage.php <coverage-dir> <clover-output>
 */

use SebastianBergmann\CodeCoverage\Report\Clover;

require dirname(__DIR__, 2) . '/vendor/autoload.php';

[, $dir, $output] = $argv + [null, null, null];
if ($dir === null || $output === null) {
    fwrite(STDERR, "Usage: php merge_coverage.php <coverage-dir> <clover-output>\n");
    exit(2);
}

$files = glob(rtrim($dir, '/') . '/*.cov') ?: [];
if ($files === []) {
    fwrite(STDERR, "No coverage files found in $dir\n");
    exit(1);
}

$merged = null;
foreach ($files as $file) {
    $coverage = require $file;
    if ($merged === null) {
        $merged = $coverage;
    } else {
        $merged->merge($coverage);
    }
}

(new Clover())->process($merged, $output);
