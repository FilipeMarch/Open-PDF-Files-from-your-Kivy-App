from kivymd.uix.button.button import MDFlatButton
from kivy.utils import platform
from kivymd.uix.dialog.dialog import MDDialog
if platform == "android":
    from jnius import cast
    from jnius import autoclass
    from android.permissions import request_permissions, Permission
    from android import mActivity, api_version



class Permission():
    def show_permission(self):
        self._show_validation_dialog()
    
    
    def permissions_external_storage(self, *args):
        if platform == "android":
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Environment = autoclass("android.os.Environment")
            Intent = autoclass("android.content.Intent")
            Settings = autoclass("android.provider.Settings")
            Uri = autoclass("android.net.Uri")
            if api_version > 29:
                # If you have access to the external storage, do whatever you need
                if Environment.isExternalStorageManager():

                    # If you don't have access, launch a new activity to show the user the system's dialog
                    # to allow access to the external storage
                    pass
                else:
                    try:
                        activity = mActivity.getApplicationContext()
                        uri = Uri.parse("package:" + activity.getPackageName())
                        intent = Intent(
                            Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION, uri
                        )
                        currentActivity = cast(
                            "android.app.Activity", PythonActivity.mActivity
                        )
                        currentActivity.startActivityForResult(intent, 101)
                    except:
                        intent = Intent()
                        intent.setAction(
                            Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION
                        )
                        currentActivity = cast(
                            "android.app.Activity", PythonActivity.mActivity
                        )
                        currentActivity.startActivityForResult(intent, 101)
                    self.show_permission_popup.dismiss()                  

    def _show_validation_dialog(self):
        if platform == "android":
            Environment = autoclass("android.os.Environment")
            if not Environment.isExternalStorageManager():
                self.show_permission_popup = MDDialog(
                    title="Alert",
                    text="In order to load input KML and spreadsheet file, an special permission is needed to access your device's internal storage and files.",
                    size_hint=(0.6, 0.5),
                    buttons=[
                        MDFlatButton(
                            text="Manage", on_press=self.permissions_external_storage
                        ),
                        MDFlatButton(
                            text="Decline",
                            on_release=self._close_validation_dialog,
                        ),
                    ],
                )
                self.show_permission_popup.open()
        else:
            print("it's working")

    def _close_validation_dialog(self, widget):
        """Close input fields validation dialog"""
        self.show_permission_popup.dismiss()