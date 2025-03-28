import sys
from os.path import exists,isdir, isfile, join
from string import Template

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()
mcu = board.get("build.mcu", "")
product_line = board.get("build.product_line", "")
bsp = board.get("build.bsp", "")

env.SConscript("_bare.py")

FRAMEWORK_DIR = platform.get_package_dir("framework-eg32firmlib")
assert isdir(FRAMEWORK_DIR)

ARDUINO_DIR = platform.get_package_dir("framework-arduino-eg32")
assert isdir(ARDUINO_DIR)

FRAMEWORK_LIB_DIR = join(FRAMEWORK_DIR, bsp + "_Firmware_Library", "libraries")
assert isdir(FRAMEWORK_LIB_DIR)

FRAMEWORK_MIDDLEWARE_DIR = join(FRAMEWORK_DIR, bsp + "_Firmware_Library", "middlewares")



def get_linker_script():
    ldscript = join(FRAMEWORK_LIB_DIR, "Device", "EG32M0xx", "startup", "gcc",
                    "linker", product_line + "_FLASH.ld")

    if isfile(ldscript):
        return ldscript

    sys.stderr.write("Warning! Cannot find a linker script for the required board! "+ldscript)


env.Append(
    CPPPATH=[
        join(FRAMEWORK_LIB_DIR, "CMSIS", "Core", "Include"),
        join(FRAMEWORK_LIB_DIR, "CMSIS", "Dsp", "Include"),
        join(FRAMEWORK_LIB_DIR, "CMSIS", "Core", "Include"),
        join(FRAMEWORK_LIB_DIR, "Device", "EG32M0xx"),
        join(FRAMEWORK_LIB_DIR, "EG32M0xx_LL_Driver", "inc"),
        join(FRAMEWORK_LIB_DIR, "EG32M0xx_LL_Driver", "src"),
        join(ARDUINO_DIR, "include"),
    ]
)

env.Append(
    CPPDEFINES=[
        "USE_STDPERIPH_DRIVER"
    ]
)

env.Append(
    CPPDEFINES=[
        env["BUILD_TYPE"].upper()
    ]
)

if not board.get("build.ldscript", ""):
    env.Replace(LDSCRIPT_PATH=get_linker_script())

#
# Target: Build Firmware Library
#

extra_flags = board.get("build.extra_flags", "")

libs = []

if board.get("build.eg32firmlib.custom_system_setup", "no") == "no":
    libs.append(env.BuildLibrary(
        join("$BUILD_DIR", "CMSIS"),
        join(FRAMEWORK_LIB_DIR, "Device", "EG32M0xx"),
        src_filter=[
            "+<*.c>",
            "+<startup/arm/eg32m0xx_startup.c>"
        ]
    ))

libs.append(env.BuildLibrary(
    join("$BUILD_DIR", "LL_Driver"),
    join(FRAMEWORK_LIB_DIR, "EG32M0xx_LL_Driver", "src"),
    src_filter=[
        "+<*.c>",
        "+<startup/arm/eg32m0xx_startup.c>"
    ]
))

libs.append(env.BuildLibrary(
    join("$BUILD_DIR", "arduino"),
    join(ARDUINO_DIR, "src"),
    src_filter=[
        "+<*.c>",
        "+<*.cpp>",
        "+<libcore/*.c>",
    ]
))

middlewares = env.GetProjectOption("middlewares","")
if(middlewares):
    for x in middlewares.split(","):
        print("Middleware %s referenced." % x)
        if isdir(join(FRAMEWORK_MIDDLEWARE_DIR, x.strip())) and exists(join(FRAMEWORK_MIDDLEWARE_DIR, x.strip())):
            if x == "i2c_application_library": 
                env.Append(
                    CPPPATH=[
                        join(FRAMEWORK_MIDDLEWARE_DIR, x.strip())
                    ]
                )
                libs.append(env.BuildLibrary(
                    join("$BUILD_DIR", "middleware", x.strip()),
                    join(FRAMEWORK_MIDDLEWARE_DIR, x.strip()),
                    src_filter=["+<*.c>"]
                ))
            if x == "freertos":
                env.Append(
                    CPPPATH=[
                        join(FRAMEWORK_MIDDLEWARE_DIR, x.strip(), "source", "include"),
                        join(FRAMEWORK_MIDDLEWARE_DIR, x.strip(), "source", "portable", "GCC", "ARM_CM3")
                    ]
                )
                libs.append(env.BuildLibrary(
                    join("$BUILD_DIR", "middleware", x.strip()),
                    join(FRAMEWORK_MIDDLEWARE_DIR, x.strip(), "source"),
                    src_filter=[
                        "+<*.c>",
                        "+<portable/common/*.c>",
                        "+<portable/gcc/ARM_CM3/*.c>"
                    ]
                ))
        else:
            sys.stderr.write("Middleware %s not exist.\r\n" % x)

env.Append(LIBS=libs)
