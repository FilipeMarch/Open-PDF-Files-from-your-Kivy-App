
https://user-images.githubusercontent.com/23220309/120887558-fb4a9700-c5c9-11eb-96a8-ac5f26718ece.mp4

# Open-PDF-Files-from-your-Kivy-App
Minimal Kivy App for Opening PDF Files 

![image](https://user-images.githubusercontent.com/23220309/120886792-1e734780-c5c6-11eb-982d-5a6cecb60d4a.png)

Requirements:
- Kivy
- Buildozer

Follow these instructions:


1) Connect your Android device to your computer
2) Download this repository folder, open it on terminal, type `buildozer -v android debug deploy run logcat` and press enter
3) Once the compilation ends, enter on the folder `.buildozer/android/platform/python-for-android/pythonforandroid/bootstraps/sdl2/build/src/main/res`
4) Paste `xml` folder from this repository on it
5) Enter on folder `.buildozer/android/platform/python-for-android/pythonforandroid/bootstraps/sdl2/build/templates`
6) Replace **AndroidManifest.tmpl.xml** by *AndroidManifest.tmpl.xml* from this repository
7) Compile the app again: `buildozer -v android debug deploy run logcat`
8) Done!

## ATTENTION ## This is working only for Android 10 or lower. 
Soon I will update this repo so this will also work for Android 11 or higher
