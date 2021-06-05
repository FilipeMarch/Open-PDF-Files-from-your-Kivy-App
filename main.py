from kivy.app import App
from kivy.lang import Builder
from kivy.utils import platform
from threading import Thread
from shutil import copyfile

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
        on_release: app.open_pdf_file()
"""


class MyApp(App):
    def build(self):
        return Builder.load_string(KV)

    def open_pdf_file(self):
        pdf_file_name = 'message.pdf'

        if platform == 'android':
            from android.storage import primary_external_storage_path
            from jnius import cast
            from jnius import autoclass
            
            downloads_folder = primary_external_storage_path() + '/Download'
            pdf_file_path = f'{downloads_folder}/{pdf_file_name}'

            # Copying File to Download folder, this will work only on Android 10 or lower
            copyfile(pdf_file_name, pdf_file_path)

            File = autoclass('java.io.File') 
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
            Context = autoclass("android.content.Context")

            Intent = autoclass('android.content.Intent')
            intent = Intent(Intent.ACTION_VIEW)
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION)

            FileProvider = autoclass('androidx.core.content.FileProvider')
            uri = FileProvider.getUriForFile(Context.getApplicationContext(), Context.getApplicationContext().getPackageName() + '.fileprovider', File(pdf_file_path))
            intent.setData(uri)

            Thread(target = lambda: self.start_intent(currentActivity, intent)).start()

        else:
            import webbrowser, os
            webbrowser.open(f'file://{os.getcwd()}/{pdf_file_path}')
    
    def start_intent(self, currentActivity, intent):
        currentActivity.startActivity(intent)


MyApp().run()
