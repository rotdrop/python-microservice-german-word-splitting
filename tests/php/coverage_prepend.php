<?php
/**
 * auto_prepend_file for the PHP built-in server used in the proxy tests.
 *
 * Collects coverage of php/proxy.php for each request and stores it in
 * PHP_PROXY_COVERAGE_DIR; merge_coverage.php combines the files afterwards.
 */

use SebastianBergmann\CodeCoverage\CodeCoverage;
use SebastianBergmann\CodeCoverage\Driver\Selector;
use SebastianBergmann\CodeCoverage\Filter;
use SebastianBergmann\CodeCoverage\Report\PHP as PhpReport;

$coverageDir = getenv('PHP_PROXY_COVERAGE_DIR');
if ($coverageDir === false || $coverageDir === '') {
    return;
}

require dirname(__DIR__, 2) . '/vendor/autoload.php';

$filter = new Filter();
$filter->includeFile(dirname(__DIR__, 2) . '/php/proxy.php');
$coverage = new CodeCoverage((new Selector())->forLineCoverage($filter), $filter);
$coverage->start('request');

register_shutdown_function(static function () use ($coverage, $coverageDir): void {
    $coverage->stop();
    (new PhpReport())->process(
        $coverage,
        $coverageDir . '/' . uniqid('request-', true) . '.cov'
    );
});
