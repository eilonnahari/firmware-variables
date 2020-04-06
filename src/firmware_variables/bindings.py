from ctypes import WINFUNCTYPE, windll, create_string_buffer, pointer, WinError, get_last_error
from ctypes.wintypes import LPCSTR, LPVOID, DWORD, PDWORD
from enum import IntFlag


GLOBAL_NAMESPACE = "{8BE4DF61-93CA-11d2-AA0D-00E098032B8C}"

ERROR_BUFFER_TOO_SMALL = 122


class Attributes(IntFlag):
    NON_VOLATILE = 0x00000001
    BOOT_SERVICE_ACCESS = 0x00000002
    RUNTIME_ACCESS = 0x00000004
    HARDWARE_ERROR_RECORD = 0x00000008
    AUTHENTICATED_WRITE_ACCESS = 0x00000010
    TIME_BASED_AUTHENTICATED_WRITE_ACCESS = 0x00000020
    APPEND_WRITE = 0x00000040


DEFAULT_ATTRIBUTES = Attributes.NON_VOLATILE | \
                     Attributes.BOOT_SERVICE_ACCESS | \
                     Attributes.RUNTIME_ACCESS


def generate_stdcall_binding(lib, name, return_type, params):
    prototype = WINFUNCTYPE(return_type, *(e[0] for e in params))
    paramflags = tuple((1, e[1]) for e in params)
    return prototype((name, lib), paramflags)


def get_firmware_environment_variable_ex_a(*args):
    func = generate_stdcall_binding(
        lib=windll.kernel32,
        name="GetFirmwareEnvironmentVariableExA",
        return_type=DWORD,
        params=(
            (LPCSTR, "name"),
            (LPCSTR, "guid"),
            (LPVOID, "buffer"),
            (DWORD, "size"),
            (PDWORD, "attributes")
        ))
    return func(*args)


def set_firmware_environment_variable_ex_a(*args):
    func = generate_stdcall_binding(
        lib=windll.kernel32,
        name="SetFirmwareEnvironmentVariableExA",
        return_type=DWORD,
        params=(
            (LPCSTR, "name"),
            (LPCSTR, "guid"),
            (LPVOID, "value"),
            (DWORD, "size"),
            (DWORD, "attributes")
        ))
    return func(*args)


def get_variable(name, namespace=GLOBAL_NAMESPACE):
    allocation = 16

    while True:
        attributes = DWORD(0)
        buffer = create_string_buffer(allocation)
        stored_bytes = get_firmware_environment_variable_ex_a(
            name.encode(),
            namespace.encode(),
            pointer(buffer),
            len(buffer),
            pointer(attributes))

        if stored_bytes != 0:
            return buffer.raw[:stored_bytes], Attributes(attributes.value)
        elif stored_bytes == 0 and get_last_error() == ERROR_BUFFER_TOO_SMALL:
            allocation *= 2
        else:
            raise WinError()


def set_variable(name, value, namespace=GLOBAL_NAMESPACE, attributes=DEFAULT_ATTRIBUTES):
    attributes = DWORD(attributes)
    res = set_firmware_environment_variable_ex_a(
        name.encode(),
        namespace.encode(),
        value,
        len(value),
        attributes)
    if res == 0:
        raise WinError()


def delete_variable(name, *args):
    set_variable(name, value=b"", *args)
