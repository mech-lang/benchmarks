using PackageCompiler

length(ARGS) == 4 || error("Expected package, bundle, training file and executable name")
package_dir, bundle_dir, training_file, executable_name = ARGS
println("Julia version: ", VERSION)
println("PackageCompiler version: ", pkgversion(PackageCompiler))
create_app(package_dir, bundle_dir;
    executables = [executable_name => "julia_main"],
    incremental = false,
    filter_stdlibs = false,
    cpu_target = "native",
    precompile_execution_file = training_file,
    sysimage_build_args = `-O3 --compile=all --strip-ir`,
    force = false,
)
