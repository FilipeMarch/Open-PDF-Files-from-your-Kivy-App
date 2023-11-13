Open a pdf file from Kivy in any android version.

#### On this video, I'm testing on Android 13, Android 10 and Android 12 respectively.
https://github.com/FilipeMarch/Open-PDF-Files-from-your-Kivy-App/assets/23220309/2d6ed3cc-a115-48e1-9ac3-afde1762404f


# Open-PDF-Files-from-your-Kivy-App
Minimal Kivy App for Opening PDF Files 

![image](https://user-images.githubusercontent.com/23220309/120886792-1e734780-c5c6-11eb-982d-5a6cecb60d4a.png)

Requirements:
- Kivy
- Buildozer

Follow these instructions:


1) Connect your Android device to your computer
2) Download this repository folder, open it on terminal, type `buildozer -v android debug deploy run logcat` and press enter
3) Enter on folder `.buildozer/android/platform/build-x86_x86_64_arm64-v8a_armeabi-v7a/dists/myapp/templates/`
4) Replace **AndroidManifest.tmpl.xml** by *AndroidManifest.tmpl.xml* from this repository
5) Compile the app again: `buildozer -v android debug deploy run logcat`
6) Done!
