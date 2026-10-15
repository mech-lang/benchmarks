"""Rebol extension entrypoint with typed Mach-O roots and frozen walk semantics."""
import argparse
import hashlib
import os
from pathlib import Path
import stat
import sys
import types

ROOT = Path('/private/tmp/mech-benchmark-completion')
ORIGINAL = ROOT/'tools/qualification/rebol_extension.py'
ORIGINAL_SHA = '8bfd7b7def7562ca810ce633dc5b92455fb29df66fc3a727641ffcc62b516493'
INSPECTOR_SHA = '877bda82e014e16a5380cc46b283ba90dca71f02c4a285994df5c54ab883489a'


def checked(path, expected):
    path = Path(path)
    if not path.is_absolute() or path.resolve() != path:
        raise ValueError('Physical adapter/controller source required')
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError('Regular adapter/controller source required')
    fd = os.open(path, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        held = os.fstat(stream.fileno())
        if (held.st_dev,held.st_ino) != (before.st_dev,before.st_ino):
            raise ValueError('Source replaced before read')
        raw = stream.read()
        after = path.lstat()
        if (held.st_dev,held.st_ino,held.st_size,held.st_mtime_ns) != (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):
            raise ValueError('Source changed during read')
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('Explicit reviewed adapter/controller digest required')
    return raw


def tool_closure(inspector, roots, pins):
    """The frozen walk, with type 2 executable/type 6 regular-library roots.

    Uses the unchanged parser, path expansion, pinning and OS boundary. A dylib
    need not have executable filesystem mode; it is read as a Mach-O image.
    Nothing is launched, chmodded, or claimed as an actual loaded-image set.
    """
    require, physical, pin = inspector.require, inspector.physical, inspector.pin
    macho, expand, os_image = inspector.macho, inspector.expand, inspector.os_image
    images, edges, aliases, system, unavailable = {}, [], {}, set(), set()
    for executable in roots:
        physical(executable)
        require(stat.S_ISREG(executable.lstat().st_mode), 'Regular Mach-O root required')
        root_type = macho(executable)['filetype']
        require(root_type in (2,6), 'Only executable or dylib roots are supported')
        require(root_type == 6 or os.access(executable,os.X_OK), 'Mach-O executable root is not executable')
        pending = [(executable, ())]; visited = set()
        while pending:
            image, inherited = pending.pop(0)
            key = (str(image),inherited)
            if key in visited: continue
            visited.add(key); require(len(visited) <= 128, 'Unbounded declared tool dependency graph')
            pin(pins,image); info = macho(image)
            images[str(image)] = dict(sha256=pins[str(image)], bytes=image.stat().st_size, load_commands=info)
            paths = tuple(dict.fromkeys([str(expand(n,image,executable)) for n in info['rpaths']]+list(inherited)))
            for item in info['imports']:
                name = item['install_name']
                if name.startswith('@rpath/'):
                    candidates = [Path(os.path.normpath(Path(p)/name[len('@rpath/'):])) for p in paths]
                else: candidates = [expand(name,image,executable)]
                for candidate in candidates:
                    if not os_image(str(candidate)) and not candidate.is_file():
                        require(not os.path.lexists(candidate), 'Nonregular or dangling loader candidate')
                        unavailable.add(str(candidate))
                available = [p for p in candidates if os_image(str(p)) or p.is_file()]
                require(all(os_image(str(p)) or not os_image(str(p.resolve())) for p in available),
                        'Non-OS loader alias into OS-managed image is unsupported')
                targets = {str(p) if os_image(str(p)) else str(p.resolve()) for p in available}
                require(len(targets) == 1, 'Missing or ambiguous declared dependency: '+name)
                target = targets.pop()
                edges.append(dict(executable=str(executable),image=str(image),install_name=name,
                                  command=item['command'],target=target,os_managed=os_image(target)))
                if os_image(target): system.add(target); continue
                for alias in available:
                    aliases[str(alias)] = str(alias.resolve())
                    pin(pins,alias)
                target_path = Path(target); physical(target_path)
                pending.append((target_path,paths))
    return dict(scope='static Mach-O declared transitive non-OS load dependencies; not actual loaded images',
                images=images,edges=edges,named_path_resolutions=aliases,unavailable_candidates=sorted(unavailable),
                os_managed_install_names=sorted(system),
                os_boundary='OS images/dyld shared cache recorded by install name, not newly file-hashed',
                actual_loaded_images_observed=False)


def attach(controller, adapter_ref):
    """Change only private module instances; keep every frozen source intact."""
    original_support, original_plan = controller.load_support, controller.build_plan

    def support(pins, resolutions):
        controller.pin(pins,resolutions,adapter_ref['path'],adapter_ref['sha256'])
        inspector = original_support(pins,resolutions)
        controller.require(controller.INSPECTOR_SHA == INSPECTOR_SHA, 'Frozen inspector identity differs')
        inspector.tool_closure = lambda roots, image_pins: tool_closure(inspector,roots,image_pins)
        return inspector

    def plan(output, intake_ref, source_ref, intake, pins, resolutions, inspector):
        controller.require(intake.get('typed_image_adapter') == adapter_ref, 'Intake must bind this exact typed-image adapter')
        controller.pin(pins,resolutions,adapter_ref['path'],adapter_ref['sha256'])
        value = original_plan(output,intake_ref,source_ref,intake,pins,resolutions,inspector)
        value['typed_image_adapter'] = dict(adapter_ref)
        value['entrypoint'] = adapter_ref['path']
        return value

    controller.load_support, controller.build_plan = support, plan
    controller.TYPED_IMAGE_ADAPTER = dict(adapter_ref)
    return controller


def load_controller(expected_adapter_sha):
    source = Path(__file__).resolve()
    checked(source,expected_adapter_sha)
    raw = checked(ORIGINAL,ORIGINAL_SHA)
    controller = types.ModuleType('rebol_original_extension_typed_images')
    controller.__file__ = str(ORIGINAL)
    exec(compile(raw,str(ORIGINAL),'exec'),controller.__dict__)
    return attach(controller,dict(path=str(source),sha256=expected_adapter_sha))


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--adapter-sha256',required=True)
    args, remaining = parser.parse_known_args()
    controller = load_controller(args.adapter_sha256)
    previous = sys.argv
    try:
        sys.argv = [previous[0],*remaining]
        controller.main()
    finally:
        sys.argv = previous


if __name__ == '__main__':
    main()
