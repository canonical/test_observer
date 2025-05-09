# Test Observer Frontend

The frontend of Test Observer is a web application developed in Flutter.

## Setup

Install flutter snap:

```bash
$ sudo snap install flutter --classic
```

Check the version of flutter installed:

```bash
$ flutter --version
```

Change flutter to the version used in production (note that the below directory doesn't get created until you run some flutter command like `flutter --version`):

```bash
$ cd ~/snap/flutter/common/flutter
$ git checkout 3.24.5
```

Then install dependencies via:
```bash
$ flutter pub get
```

And finally, make sure to install chrome.

## Run

This project uses code generation, so you must first generate the required code:

```bash
$ dart run build_runner build
```

Then you can launch the fontend on chrome:

```bash
$ flutter run -d chrome
```

## Test

### Static analysis

```bash
$ flutter analyze
```

### Unit tests

```bash
$ flutter test --platform chrome # requires chrome
```

### Integration tests

To run integration tests you first need to install chromedriver.

Then you can run it via:
```bash
$ chromedriver --port=4444
```

While it's running you can launch a single integration test via:
```bash
$ flutter drive --driver=test_driver/integration_test.dart --target=integration_test/<integration-test-file> -d chrome
```

You can even run it in headless mode via:
```bash
$ flutter drive --driver=test_driver/integration_test.dart --target=integration_test/<integration-test-file> -d web-server
```

And you can run all integration tests via the bash script:
```bash
$ ./run_integration_tests.sh
```

## Benchmark

There are some benchmarks written under the `/benchmarks` directory. You can run these using:

```bash
$ dart run_benchmark_tests.dart
```

This will open up chrome and run the benchmarks infront of you.

You can also pass `--headless` to run the above command in headless mode.

Either way the command will produce json files with results under the `/benchmarks` directory.

## Connect to backend

By default the Test Observer frontend will use `http://localhost:30000/` to communicate with the backend. To use a different address you can modify `window.testObserverAPIBaseURI` attribute in `web/index.html`.