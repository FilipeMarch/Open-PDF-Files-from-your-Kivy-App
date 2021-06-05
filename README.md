# Open-PDF-Files-from-your-Kivy-App
Minimal Kivy App for Opening PDF Files 

![image](https://user-images.githubusercontent.com/23220309/120886792-1e734780-c5c6-11eb-982d-5a6cecb60d4a.png)

Follow these instructions:


1) Connect your Android device to your computer
2) Download this repository folder, open it on terminal, type `buildozer -v android debug deploy run logcat` and press enter
3) Once the compilation ends, enter on the folder `.buildozer/android/platform/python-for-android/pythonforandroid/bootstraps/sdl2/build/src/main`
4) Paste `xml` folder from this repository on it
5) Enter on folder `.buildozer/android/platform/python-for-android/pythonforandroid/bootstraps/sdl2/build/templates`
6) Replace **AndroidManifest.tmpl.xml** by the same file from this repository
7) Compile the app again: `buildozer -v android debug deploy run logcat`
