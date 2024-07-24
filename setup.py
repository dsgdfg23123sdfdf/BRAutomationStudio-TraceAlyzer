from py2exe.build_exe import freeze

options = {
    "bundle_files": 1,  # Bundle everything, including the Python interpreter.
    "compressed": True  # Compress the library archive.
}

freeze(
    windows=[{'script': "traceAnalyzer.py"}],
    options={'py2exe': options},
    zipfile=None  # Append the library to the executable.
)