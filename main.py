from shutil import copyfile
from threading import Thread

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.utils import platform

if platform == "android":
    from android.permissions import Permission, request_permissions
    from android.storage import primary_external_storage_path
    from jnius import autoclass, cast

KV = """
BoxLayout:
    orientation: 'vertical'
    padding: dp(10)
    
    Image:
        source: 'kivy-pdf.png'

    Button:
        text: 'Open PDF file'
        size_hint: 0.4, 0.1
        pos_hint: {'center_x': 0.5}
        on_release: app.ask_permissions()
"""


class MyApp(App):
    def build(self):
        return Builder.load_string(KV)

    def get_android_version(self):
        if platform == "android":
            VERSION = autoclass("android.os.Build$VERSION")
            android_version = int(VERSION.RELEASE.split(".")[0])
            return android_version

    def ask_permissions(self):
        from android.permissions import Permission, request_permissions

        request_permissions(
            [Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE],
            self.on_permissions_callback,
        )

    def on_permissions_callback(self, permissions, results):
        print("Permissions:", permissions, "Results:", results)
        if all([res for res in results]):
            self.open_pdf_file()

    def open_pdf_file(self):
        android_version = self.get_android_version()
        pdf_file_name = "message.pdf"

        if platform == "android":
            self.open_pdf_file_android(pdf_file_name, android_version)
        else:
            self.open_pdf_file_desktop(pdf_file_name)

    def open_pdf_file_desktop(self, pdf_file_name):
        import os
        import webbrowser

        webbrowser.open(f"file://{os.getcwd()}/{pdf_file_name}")

    def open_pdf_file_android(self, pdf_file_name, android_version):
        File = autoclass("java.io.File")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context = autoclass("android.content.Context")
        Intent = autoclass("android.content.Intent")
        intent = Intent(Intent.ACTION_VIEW)
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
        currentActivity = cast("android.app.Activity", PythonActivity.mActivity)

        if android_version < 10:
            # Using legacy external storage (Android 9 or lower)
            # i.e., not scoped storage (https://developer.android.com/training/data-storage/use-cases)
            downloads_folder = primary_external_storage_path() + "/Download"
            pdf_file_path = f"{downloads_folder}/{pdf_file_name}"

            copyfile(pdf_file_name, pdf_file_path)

            FileProvider = autoclass("androidx.core.content.FileProvider")
            context = cast(Context, currentActivity.getApplicationContext())
            package_name = context.getPackageName()

            uri = FileProvider.getUriForFile(
                context, package_name + ".fileprovider", File(pdf_file_path)
            )
        else:
            # Using scoped storage (Android 10 or higher)
            # We first delete the file from the Download folder (if it exists)
            # and then insert it to the Download folder
            from storage import SharedStorage

            storage = SharedStorage()
            storage.delete(pdf_file_name, "Download")
            storage.insert(pdf_file_name, "Download")
            storage.retrieve(pdf_file_name, "Download")
            uri = storage.getUri(pdf_file_name, "Download")
            print("uri: ", uri)

        intent.setData(uri)

        Thread(target=lambda: self.start_intent(currentActivity, intent)).start()

    def start_intent(self, currentActivity, intent):
        currentActivity.startActivity(intent)


MyApp().run()
