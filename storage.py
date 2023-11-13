from os import W_OK, access, mkdir, remove
from os.path import basename, exists, join, splitext
from shutil import copy

from android import api_version, autoclass, cast, mActivity
from android.storage import primary_external_storage_path

FileOutputStream = autoclass("java.io.FileOutputStream")
FileInputStream = autoclass("java.io.FileInputStream")
ByteArrayOutputStream = autoclass("java.io.ByteArrayOutputStream")
FileUtils = autoclass("android.os.FileUtils")
Environment = autoclass("android.os.Environment")
MediaStoreFiles = autoclass("android.provider.MediaStore$Files")
MediaStoreAudioMedia = autoclass("android.provider.MediaStore$Audio$Media")
MediaStoreImagesMedia = autoclass("android.provider.MediaStore$Images$Media")
MediaStoreVideoMedia = autoclass("android.provider.MediaStore$Video$Media")
if api_version > 28:
    MediaStoreDownloads = autoclass("android.provider.MediaStore$Downloads")
MediaStoreMediaColumns = autoclass("android.provider.MediaStore$MediaColumns")
ContentValues = autoclass("android.content.ContentValues")
MimeTypeMap = autoclass("android.webkit.MimeTypeMap")
JString = autoclass("java.lang.String")
Uri = autoclass("android.net.Uri")
ContentUris = autoclass("android.content.ContentUris")
# StreamCopy = autoclass('org.kivy.storage.StreamCopy')

# Source https://github.com/RobertFlatt/Android-for-Python/storage

#########################
# assumes build api>=29
# api=30 recomended
#########################


class SharedStorage:
    # For shared media, documents, and downloads
    ############################################
    #
    # Shared Storage is a database, NOT a Linux file system.
    # See notes below about implementation differences for devices using
    # api <29
    #
    # The database is organized in Root Directories
    #  'Music'
    #  'Movies'
    #  'Pictures'
    #  'Documents'
    #  '*'             (default) one of the first 4 depending on file extension
    #  'Downloads'
    #  'DCIM'          For retrive of camera data.
    #
    #  Within those Root Directories this app's public files are stored under
    #  its 'AppName'. Sub-directories are available.
    #
    # The database operations 'insert', 'retrieve', and 'delete' are
    # implemented. An insert overwrites an existing entry. Retrieve from
    # storage created by other apps requires READ_EXTERNAL_STORAGE
    #
    # Entries are defined by Root Directory, optional sub-directory, and file
    # name.
    #
    # Entries persist after this app is uninstalled.
    #
    # The api defaults to the 'external' volume, 'internal' is available.
    #
    # Device api<29 requires WRITE_EXTERNAL_STORAGE
    #
    # Files in 'Downloads' do not have a uri if device api < 29
    #
    # Two additional methods enable interoperability with the Android
    # 'android.net.Uri' class.
    #
    # ######## Android Version Transition, Read me, Really ###############
    #
    # The api above is consistent from device api = 21 to at least api = 30.
    # However the internal implementation is different between devices with
    # api >= 29 and api < 29. This is a characteristic of Android storage.
    # See for example
    #  https://www.raywenderlich.com/10217168-preparing-for-scoped-storage
    #
    # On new Android versions the file is owned by the database, on older
    # Android versions the file is owned by the app.
    # Thus when device api < 29 , a file can be deleted by the user but the
    # data base entry may still exist. And retrieve() will return ""
    #
    # On newer devices the datebase key for file path is RELATIVE_PATH
    # on older devices it is DATA which is now depreciated.
    #
    # The two implementations require special handling of the user's
    # data when the user moves files to a platorm with api >= 29 from one with
    # api < 29. This is a general Android issue and not specific to this
    # module.
    #
    # The transition handling might involve:
    # Before transition 1) Copy the app's shared files to private storage.
    #                   2) Delete the app's database entries
    # After transition  3) Insert the copies into the database
    #                   4) Delete the copied files.
    # If 1) and 2) are done after the transition, before doing 3) manually
    # delete the shared files
    #
    ###################
    #
    # Database Operations:
    # insert()      - copy a PrivateStorage file into this app's SharedStorage.
    # retrieve()    - copy a SharedStorage file to PrivateStorage on device
    #                 api>= 29 and return a file path, else return a file path.
    # delete()      - delete a file in this app's SharedStorage.
    #
    # Interoperability with Android 'android.net.Uri' class:
    # getUri()      - get a Uri from SharedStorage path,          returns Uri
    # retrieveUri() - copy SharedStorage Uri to PrivateStorage,
    #                  returns a file path
    #
    ###################
    # The API:
    #
    # insert(file_path,
    #        root_dir = '*',
    #        sub_dir = '',
    #        volume = 'external')
    #               returns True if file inserted
    #
    # retrieve(file_name
    #        root_dir = '*'
    #        sub_dir = '',
    #        app_name = '',    requires READ_EXTERNAL_STORAGE
    #        volume = 'external')
    #                returns a PrivateStorage file path, or a URL string
    #
    # delete(file_name,
    #        root_dir = '*',
    #        sub_dir = '',
    #        volume = 'external')
    #                 returns True if file exists to delete
    #
    # getUri(file_name,
    #        root_dir = '*',
    #        sub_dir = '',
    #        app_name = '',    requires READ_EXTERNAL_STORAGE
    #        volume = 'external')
    #                   returns a Uri ('android.net.Uri')
    #                   Except if 'Downloads' and device api <29, returns None
    #
    # retrieveUri(uri) #A 'android.net.Uri' from some other Android Activity
    #                   returns a PrivateStorage file path.
    #
    #######################
    #
    # Examples:
    # Where txt_file could be PrivateStorage().getFilesDir() + 'text.txt'
    # and so on.
    # All methods take a required file name, and optional directory parameters.
    #
    #   Insert:
    #   SharedStorage().insert(txt_file, 'Documents')
    #   SharedStorage().insert(txt_file, sub_dir= 'a/b')
    #   SharedStorage().insert(txt_file, 'Downloads')
    #   SharedStorage().insert(jpg_file, 'Pictures')
    #   SharedStorage().insert(mp3_file)
    #   SharedStorage().insert(ogg_file, 'Music')
    #
    #   Retrieve:
    #   path = SharedStorage().retrieve('test.txt')
    #   path = SharedStorage().retrieve('test.txt', 'Documents', 'a/b')
    #
    #   Delete:
    #   SharedStorage().delete('test.mp3', 'Music')
    #
    #   Retrieve from another app's storage (requires READ_EXTERNAL_STORAGE) :
    #   SharedStorage().retrieve('10_28_14.jpg', 'DCIM', '2021_03_12',
    #                            'CameraXF')
    #   SharedStorage().retrieve('10_33_48.mp4', 'DCIM', '2021_03_12',
    #                            'CameraXF')
    #
    #######################

    # saves a copy of a PrivateStorage file to SharedStorage, return success
    def insert(self, file_path, root_dir="*", sub_dir="", volume="external"):
        success = False
        try:
            volume = volume.lower()
            if volume not in ["internal", "external"]:
                volume = "external"
            file_name = basename(file_path)
            self.delete(file_name, root_dir, sub_dir, volume)
            # build MediaStore data for everything except Downloads on api< 29
            MIME_type = self._get_file_MIME_type(file_name)
            root_directory = self._get_root_directory(root_dir, MIME_type)
            sub_directory = join(root_directory, self._app_name())
            if sub_dir:
                sub_directory = join(sub_directory, sub_dir)
            root_uri = self._get_root_uri(root_directory, volume, MIME_type)
            cv = ContentValues()
            if api_version > 28:
                if exists(join(sub_directory, file_name)) and not access(
                    join(sub_directory, file_name), W_OK
                ):
                    # the delete above failed probably due to an Android OS upgrade
                    # from <= 28 to > 28.
                    # See 'Android version transition' above
                    print(
                        "ERROR SharedStorage.insert():\n"
                        + "Unable to insert file due to Android version transition\n"
                        + "See Android Version Transition in API_STORAGE_README.txt"
                    )
                    return False
                cv.put(MediaStoreMediaColumns.DISPLAY_NAME, file_name)
                cv.put(MediaStoreMediaColumns.MIME_TYPE, MIME_type)
                cv.put(MediaStoreMediaColumns.RELATIVE_PATH, sub_directory)
                # copy file
                context = mActivity.getApplicationContext()
                uri = context.getContentResolver().insert(root_uri, cv)
                ws = context.getContentResolver().openOutputStream(uri)
                rs = FileInputStream(file_path)
                FileUtils.copy(rs, ws)
                ws.flush()
                ws.close()
                rs.close()
                success = bool(self.getUri(file_name, root_dir, sub_dir, "", volume))
            else:
                sub_directory = self._create_pre_29_directory(root_directory, sub_dir)
                copy(file_path, sub_directory)
                new_file_path = join(sub_directory, file_name)
                if root_directory == Environment.DIRECTORY_DOWNLOADS:
                    success = exists(new_file_path)
                else:
                    cv.put(MediaStoreMediaColumns.DISPLAY_NAME, file_name)
                    cv.put(MediaStoreMediaColumns.DATA, new_file_path)
                    context = mActivity.getApplicationContext()
                    uri = context.getContentResolver().insert(root_uri, cv)
                    success = exists(file_path) and bool(uri)
        except Exception as e:
            print("ERROR SharedStorage.insert():\n" + str(e))
        return success

    # delete SharedStorage entry, only for this app's entries
    def delete(self, file_name, root_dir="*", sub_dir="", volume="external"):
        success = False
        try:
            fileUri = self.getUri(file_name, root_dir, sub_dir, "", volume)
            if fileUri:
                context = mActivity.getApplicationContext()
                context.getContentResolver().delete(fileUri, None, None)
                success = True
            if not fileUri or api_version < 29:
                # Not in the database, but a file might exist at the location
                # equivalent to the database reference.
                # So an insert would add a versioned display name 'xxx (n).yy'
                # And this would break the 'replace' model we assume.
                # Explicitly look for and remove the file system entry.
                #
                # If device api < 29 then the file is not removed by the
                # database delete(), so explicitly remove if present.
                if not primary_external_storage_path():
                    return success
                file_path = self._equivalent_file(file_name, root_dir, sub_dir)
                if exists(file_path):
                    # write access ?
                    if access(file_path, W_OK):
                        remove(file_path)
                    success = not exists(file_path)
        except Exception as e:
            print("ERROR SharedStorage.delete():\n" + str(e))
        return success

    # copy SharedStorage entry to PrivateStorage cacheDir, return its file_path
    def retrieve(
        self, file_name, root_dir="*", sub_dir="", app_name="", volume="external"
    ):
        result = ""
        if api_version > 28:
            uri = self.getUri(file_name, root_dir, sub_dir, app_name, volume)
            result = self.retrieveUri(uri)
        else:
            # don't need the db to find the file, we know where it is.
            if not primary_external_storage_path():
                return result
            file_path = self._equivalent_file(file_name, root_dir, sub_dir, app_name)
            if exists(file_path):
                new_file_path = self._save_to()
                copy(file_path, new_file_path)
                result = join(new_file_path, file_name)
        return result

    # from Android 'android.net.Uri' class
    # for 'content' and 'file' uris copy the file to PrivateStorage
    # for other uris retun the uri as a string
    def retrieveUri(self, someUri):
        new_file_path = ""
        try:
            if someUri:
                someUri = cast("android.net.Uri", someUri)
                scheme = someUri.getScheme().lower()
                if scheme == "content":
                    context = mActivity.getApplicationContext()
                    cursor = context.getContentResolver().query(
                        someUri, None, None, None, None
                    )
                    dn = MediaStoreMediaColumns.DISPLAY_NAME
                    nameIndex = cursor.getColumnIndex(dn)
                    cursor.moveToFirst()
                    file_name = cursor.getString(nameIndex)
                    new_file_path = join(self._save_to(), file_name)
                    cr = mActivity.getContentResolver()
                    rs = cr.openInputStream(someUri)
                    if api_version > 28:
                        ws = FileOutputStream(new_file_path)
                        FileUtils.copy(rs, ws)
                        ws.flush()
                        ws.close()
                    rs.close()
                    cursor.close()
                elif scheme == "file":
                    new_file_path = someUri.getPath()
                else:
                    # https://en.wikipedia.org/wiki/List_of_URI_schemes
                    new_file_path = someUri.toString()
        except Exception as e:
            print("ERROR SharedStorage.retrieveUri():\n" + str(e))
        return new_file_path

    # get a Java android.net.Uri
    def getUri(
        self, file_name, root_dir="*", sub_dir="", app_name="", volume="external"
    ):
        fileUri = None
        try:
            if api_version < 29 and root_dir.lower() in ["downloads", "download"]:
                return None
            volume = volume.lower()
            if volume not in ["internal", "external"]:
                volume = "external"
            MIME_type = self._get_file_MIME_type(file_name)
            root_direct = self._get_root_directory(root_dir, MIME_type)
            root_uri = self._get_root_uri(root_direct, volume, MIME_type)
            location = root_direct
            if app_name:
                location = join(location, app_name)
            else:
                location = join(location, self._app_name())
            if sub_dir:
                location = join(location, sub_dir)
            selection = (
                MediaStoreMediaColumns.DISPLAY_NAME + " LIKE '" + file_name + "'"
            )
            selection += " AND "
            if api_version > 28:
                selection += (
                    MediaStoreMediaColumns.RELATIVE_PATH + " LIKE '" + location + "/'"
                )
            else:
                path = self._get_pre_29_directory(root_direct, sub_dir, app_name)
                file_path = join(path, file_name)
                selection += MediaStoreMediaColumns.DATA + " LIKE '" + file_path + "'"
            context = mActivity.getApplicationContext()
            cursor = context.getContentResolver().query(
                root_uri, None, selection, None, None
            )
            while cursor.moveToNext():
                dn = MediaStoreMediaColumns.DISPLAY_NAME
                index = cursor.getColumnIndex(dn)
                fileName = cursor.getString(index)
                """
                # For debugging
                if api_version < 29:
                    ddn = MediaStoreMediaColumns.DATA
                else:
                    ddn = MediaStoreMediaColumns.RELATIVE_PATH
                dindex = cursor.getColumnIndex(ddn)
                dataName = cursor.getString(dindex)
                """
                if file_name == fileName:
                    id_index = cursor.getColumnIndex(MediaStoreMediaColumns._ID)
                    id = cursor.getLong(id_index)
                    fileUri = ContentUris.withAppendedId(root_uri, id)
                    break
            cursor.close()

        except Exception as e:
            print("ERROR SharedStorage.getUri():\n" + str(e))
        return fileUri

    ###########
    # utilities
    ###########

    def _equivalent_file(self, file_name, root_dir, sub_dir, app_name=""):
        MIME_type = self._get_file_MIME_type(file_name)
        root_direct = self._get_root_directory(root_dir, MIME_type)
        path = self._get_pre_29_directory(root_direct, sub_dir, app_name)
        return join(path, file_name)

    def _get_pre_29_directory(self, root, sub_dir, app_name=""):
        directory = join(primary_external_storage_path(), root)
        if app_name:
            directory = join(directory, app_name)
        else:
            directory = join(directory, self._app_name())
        if sub_dir:
            directory = join(directory, sub_dir)
        return directory

    def _create_pre_29_directory(self, root, sub_dir):
        directory = join(primary_external_storage_path(), root)
        if not exists(directory):
            mkdir(directory)
        # we always enable this case through the api
        directory = join(directory, self._app_name())
        if not exists(directory):
            mkdir(directory)
        if sub_dir:
            sub_dirs = sub_dir.split("/")
            for s in sub_dirs:
                directory = join(directory, s)
                if not exists(directory):
                    mkdir(directory)
        return directory

    def _save_to(self):
        new_file_loc = PrivateStorage().getCacheDir()
        if not new_file_loc:
            new_file_loc = PrivateStorage().getCacheDir("internal")
        new_file_loc = join(new_file_loc, "FromSharedStorage")
        if not exists(new_file_loc):
            mkdir(new_file_loc)
        return new_file_loc

    def _get_file_MIME_type(self, file_name):
        try:
            file_ext_no_dot = ""
            file_ext = splitext(file_name)[1]
            if file_ext:
                file_ext_no_dot = file_ext[1:]
            if file_ext_no_dot:
                lower_ext = file_ext_no_dot.lower()
                mtm = MimeTypeMap.getSingleton()
                MIME_type = mtm.getMimeTypeFromExtension(lower_ext)
                if not MIME_type:
                    MIME_type = "application/" + file_ext_no_dot
            else:
                MIME_type = "application/unknown"
        except Exception as e:
            print("ERROR SharedStorage._file_MIME_type():\n" + str(e))
            MIME_type = "application/unknown"
        return MIME_type

    def _get_root_directory(self, root_dir, MIME_type):
        if root_dir == "*":
            root, ext = MIME_type.split("/")
            if root == "image":
                root_dir = "pictures"
            elif root == "video":
                root_dir = "movies"
            elif root == "audio":
                root_dir = "music"
            else:
                root_dir = "documents"
        root_dir = root_dir.lower()
        if root_dir in ["downloads", "download"]:
            root_directory = Environment.DIRECTORY_DOWNLOADS
        elif root_dir == "pictures":
            root_directory = Environment.DIRECTORY_PICTURES
        elif root_dir == "movies":
            root_directory = Environment.DIRECTORY_MOVIES
        elif root_dir == "music":
            root_directory = Environment.DIRECTORY_MUSIC
        elif root_dir == "dcim":
            root_directory = Environment.DIRECTORY_DCIM
        else:
            root_directory = Environment.DIRECTORY_DOCUMENTS
        return root_directory

    def _get_root_uri(self, root_directory, volume, MIME_type):
        if root_directory == Environment.DIRECTORY_DOWNLOADS:
            if api_version < 29:
                root_uri = None
            else:
                root_uri = MediaStoreDownloads.getContentUri(volume)
        elif root_directory == Environment.DIRECTORY_PICTURES or (
            root_directory == Environment.DIRECTORY_DCIM and "image/" in MIME_type
        ):
            root_uri = MediaStoreImagesMedia.getContentUri(volume)
        elif root_directory == Environment.DIRECTORY_MOVIES or (
            root_directory == Environment.DIRECTORY_DCIM and "video/" in MIME_type
        ):
            root_uri = MediaStoreVideoMedia.getContentUri(volume)
        elif root_directory == Environment.DIRECTORY_MUSIC:
            root_uri = MediaStoreAudioMedia.getContentUri(volume)
        else:
            root_uri = MediaStoreFiles.getContentUri(volume)
        return root_uri

    def _app_name(self):
        context = mActivity.getApplicationContext()
        appinfo = context.getApplicationInfo()
        if appinfo.labelRes:
            name = context.getString(appinfo.labelRes)
        else:
            name = appinfo.nonLocalizedLabel.toString()
        return name


class PrivateStorage:
    # For app specific files
    # No permissions required
    # External directories that are not mounted return ''
    # FilesDir lifetime ends when app uninstalled.
    # cacheDir is temporary storage managed by Android, lifetime is undefined.
    # The install directory './' is also private storage, lifetime ends
    #   when app is updated. Use as read only of files in apk.
    # external and internal refer to the storage volume
    #
    # Examples :
    #   Install Dir:   getcwd()
    #   FilesDir:      PrivateStorage().getFilesDir()
    #   CacheDir:      PrivateStorage().getCacheDir())

    def getFilesDir(self, volume="external"):
        if volume not in ["internal", "external"]:
            volume = "external"
        context = mActivity.getApplicationContext()
        result = ""
        if volume == "internal":
            result = context.getFilesDir().toString()
        else:
            result = context.getExternalFilesDir(None)
            if result:
                result = result.toString()
        return str(result)

    def getCacheDir(self, volume="external"):
        if volume not in ["internal", "external"]:
            volume = "external"
        context = mActivity.getApplicationContext()
        result = ""
        if volume == "internal":
            result = context.getCacheDir().toString()
        else:
            result = context.getExternalCacheDir()
            if result:
                result = result.toString()
        return str(result)
