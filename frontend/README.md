# Test Observer Frontend

The frontend of Test Observer is a web application developed in Flutter.

## Setup

Follow official flutter installation [instructions](https://docs.flutter.dev/get-started/install/linux).

Then install dependencies via:
```bash
$ flutter pub get
```

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

## Connect to backend

By default the Test Observer frontend will use `http://localhost:30000/` to communicate with the backend. To use a different address you can modify `window.testObserverAPIBaseURI` attribute in `web/index.html`.