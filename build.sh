flutter pub get
dart run --suppress-analytics serious_python:main package app/src/ --platform Android -r flet-geolocator==0.1.0 -r flet-permission-handler==0.1.0 -r flet==0.27.6 -r "requests>2.26.0" -r taiwanbus==0.0.9 -r pyjnius --exclude build --compile-app --compile-packages --cleanup-packages
dart run --suppress-analytics flutter_native_splash:create
flutter build apk --no-version-check --suppress-analytics --build-name 21d96b6

# web
dart run --suppress-analytics serious_python:main package app/src/ --platform Pyodide -r flet-geolocator==0.1.0 -r flet-permission-handler==0.1.0 -r flet==0.27.6 -r "requests>2.26.0" -r taiwanbus==0.0.9 --exclude build,assets --compile-app --compile-packages --cleanup-packages
flutter build web --no-version-check --suppress-analytics --build-name 21d96b6