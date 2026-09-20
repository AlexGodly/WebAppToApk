# Web2APK Desktop

Web2APK is a Windows desktop GUI that turns a complete client-side web project into an Android APK.

## What you can put into it

Select an entire web project folder containing `index.html`, for example:

```text
MyApp/
├── index.html
├── login.html
├── css/
├── js/
├── images/
├── fonts/
└── data/
```

The entire selected folder is copied into the Android app.

Supported web-side content includes HTML, CSS, JavaScript, JSON, images, fonts, audio/video and other static assets.

Server-side code such as PHP, Python server code, Express/Node backends, MySQL servers, etc. cannot simply run inside the APK. Your web project must be able to run client-side or communicate with an external backend/API.

## Desktop app features

- Select a complete web project folder.
- Checks for `index.html`.
- Set app name.
- Set Android package ID.
- Set version name.
- Set version code.
- Set output APK filename.
- Choose a PNG/JPG launcher icon.
- Choose APK output folder.
- Environment status for Java, Node and Android SDK.
- Automatically creates an isolated Capacitor Android workspace.
- Automatically installs Android command-line tools when missing.
- Installs Android SDK platform/build tools.
- Runs Capacitor sync.
- Generates launcher icon sizes.
- Runs the Gradle build.
- Shows live build logs.
- Opens the generated APK when finished.
- Remembers your most recently used settings.

## Requirements

For running the source:

- Windows 10/11
- Python 3
- Node.js/npm
- Java JDK 21 recommended
- Internet connection for first-time dependency/SDK downloads

Android Studio is not required.

The packaged `Web2APK.exe` still needs Node.js and a Java JDK on the computer because those tools perform the Android build.

## Run from source

Double-click:

```text
RUN-WEB2APK.bat
```

If Pillow is not installed yet, install it with:

```text
py -m pip install Pillow
```

Then run the BAT again.

## Build the Windows EXE

Double-click:

```text
BUILD-WINDOWS-EXE.bat
```

The script installs PyInstaller and Pillow and creates:

```text
dist/Web2APK.exe
```

You can then launch `Web2APK.exe` like a normal Windows application.

## How to use Web2APK

1. Launch Web2APK.
2. Click **Select Folder**.
3. Choose the root folder of your web project. It must contain `index.html`.
4. Enter the visible app name.
5. Enter a package ID such as `com.alexgodly.mediaflow`.
6. Enter a version name such as `1.0.0`.
7. Enter a positive integer version code such as `1`.
8. Enter the APK output name, e.g. `MediaFlow-v1.apk`.
9. Choose a square icon. 1024×1024 PNG is recommended.
10. Choose the output folder.
11. Click **BUILD APK**.
12. Watch the Build Log. The first build can take longer because Android/Gradle dependencies are downloaded.
13. When successful, the finished APK is copied to your chosen output folder.

## Updating an existing Android app

Keep the same package ID.

Example:

```text
Old:
Package:      com.alexgodly.mediaflow
Version name: 1.0.0
Version code: 1

New:
Package:      com.alexgodly.mediaflow
Version name: 1.1.0
Version code: 2
```

Then select the updated web project and build again.

Changing the package ID makes Android treat the APK as a different app.

## Important: debug signing

This version builds a debug APK with:

```text
gradlew assembleDebug
```

That is suitable for personal installation and testing.

A future release-build feature can add:
- keystore creation/import
- signed release APK
- Android App Bundle (AAB)
- Google Play-ready builds

## Application data

Web2APK stores its own GUI settings/workspaces under:

```text
%APPDATA%\Web2APK
```

Your original selected web project is not modified. Web2APK copies it into its own temporary build workspace.

## Troubleshooting

### Java missing

Install a full JDK. The application checks common JDK locations and requires both `java.exe` and `javac.exe`.

### Node missing

Install Node.js, reopen Web2APK, and click Recheck.

### First build is slow

This is expected. npm, Android SDK packages and Gradle dependencies may need to download.

### index.html missing

Select the root of the web project, not a parent folder. The selected folder itself must contain `index.html`.

### Build fails

Read/copy the final lines in the Build Log. They contain the actual npm, Capacitor, SDK or Gradle error.
