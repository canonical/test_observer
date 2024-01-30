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

### Run tests

```bash
$ flutter test --platform chrome # requires chrome
```

## Connect to backend

By default the Test Observer frontend will use `http://localhost:30000/` to communicate with the backend. To use a different address you can modify `window.testObserverAPIBaseURI` attribute in `web/index.html`.