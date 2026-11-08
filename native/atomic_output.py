"""Publish a complete, fsynced artifact directory with Linux RENAME_NOREPLACE.

No portable fall-back silently weakens non-overwrite or atomic visibility.
Unsupported platforms fail before staging. macOS is explicitly untested.
Only the private staging directory created by this invocation is cleaned up.
"""
import ctypes
import errno
import os
from pathlib import Path
import shutil
import sys
import tempfile


class PublicationError(OSError):
    def __init__(self, message, *, final_path, published=False, staging_path=None):
        super().__init__(message)
        self.final_path = str(final_path)
        self.published = published
        self.staging_path = str(staging_path) if staging_path else None


def load_rename_noreplace():
    if not sys.platform.startswith('linux'):
        raise PublicationError('Atomic no-overwrite publication is supported only on tested Linux; no files created', final_path='')
    library = ctypes.CDLL(None, use_errno=True)
    function = getattr(library, 'renameat2', None)
    if function is None:
        raise PublicationError('Linux renameat2 is unavailable; no weaker fallback is used', final_path='')
    function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    function.restype = ctypes.c_int
    return function


def rename_noreplace(source, destination, function):
    if function(-100, os.fsencode(source), -100, os.fsencode(destination), 1) != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), str(destination))


def fsync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def identity(path):
    try:
        st = Path(path).lstat()
    except FileNotFoundError:
        return None
    return st.st_dev, st.st_ino


def validate_written(stage, outputs):
    actual = {p.name for p in stage.iterdir()}
    if actual != set(outputs):
        raise OSError(errno.EIO, 'Staging artifact inventory changed')
    for name, expected in outputs.items():
        path = stage/name
        if path.is_symlink() or path.stat().st_size != len(expected):
            raise OSError(errno.EIO, 'Staging artifact size/type mismatch: ' + name)
        with path.open('rb') as file:
            found = file.read(len(expected) + 1)
        if found != expected:
            raise OSError(errno.EIO, 'Staging artifact content mismatch: ' + name)


def publish_new_directory(destination, outputs, *, before_publish=None):
    """All writes happen in hidden staging; a complete directory is published once.

    If staging or publication fails, remove only our own staging tree. If cleanup
    itself fails, disclose its explicit partial path. A process crash may leave
    a `.origin-native-partial-*` directory, never a final-name partial artifact.
    """
    destination = Path(os.path.abspath(destination))
    if os.path.lexists(destination):
        raise ValueError('Output directory must be new')
    if not destination.parent.is_dir():
        raise ValueError('Output parent directory must already exist')
    for name, value in outputs.items():
        if Path(name).name != name or name in ('', '.', '..') or type(value) is not bytes:
            raise ValueError('Only flat byte artifacts may be published')
    rename_function = load_rename_noreplace()
    stage = Path(tempfile.mkdtemp(prefix='.origin-native-partial-', dir=destination.parent))
    stage_identity = identity(stage)
    committed = False
    recovered_publish = False
    try:
        for name, value in outputs.items():
            with (stage/name).open('xb') as file:
                written = file.write(value)
                if written != len(value):
                    raise OSError(errno.EIO, 'Short write while staging ' + name)
                file.flush()
                os.fsync(file.fileno())
        validate_written(stage, outputs)
        fsync_directory(stage)
        if before_publish is not None:
            before_publish()
        try:
            rename_noreplace(stage, destination, rename_function)
            committed = True
        except BaseException:
            # A wrapper/connection may fail after the kernel rename succeeded.
            # Check the exact directory identity before attempting any cleanup.
            if identity(destination) != stage_identity or os.path.lexists(stage):
                raise
            committed = True
            validate_written(destination, outputs)
            recovered_publish = True
        try:
            fsync_directory(destination.parent)
        except BaseException as exc:
            raise PublicationError(
                'Complete candidate is published, but directory durability sync failed; do not blindly retry: ' + str(destination),
                final_path=destination, published=True) from exc
        return {'published': True, 'atomic_no_replace': True,
                'recovered_uncertain_publish': recovered_publish,
                'final_path': str(destination)}
    except BaseException as exc:
        if committed:
            if isinstance(exc, PublicationError):
                raise
            raise PublicationError('Complete output was published before a later error; check it before retrying',
                                   final_path=destination, published=True) from exc
        cleanup_error = None
        if identity(stage) == stage_identity:
            try:
                shutil.rmtree(stage)
            except BaseException as error:
                cleanup_error = error
        if cleanup_error is not None or os.path.lexists(stage):
            raise PublicationError(
                'Generation failed before publication; incomplete hidden staging remains at ' + str(stage) + ': ' + str(exc),
                final_path=destination, staging_path=stage, published=False) from exc
        raise PublicationError('Generation failed before publication; staging cleaned; no candidate was published: ' + str(exc),
                               final_path=destination, published=False) from exc
