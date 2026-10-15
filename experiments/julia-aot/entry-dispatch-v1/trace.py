"""Draft LLDB observations for one unchanged Julia N-body process at input 1.

This module does not launch, attach, evaluate target expressions, or qualify AOT.
A reviewed owner must install it before first resuming its stopped target,
register that target and debugserver, and drive stopped()/module_event()/finished(). Native API
compatibility and that ownership integration have not yet been executed.
"""
import copy
import struct


MAIN = {
    'main': 0x100004514,
    'exported_entry': 0x10000452c,
    'entry_world_compare': 0x1000045a0,
    'entry_indirect_call': 0x1000045c4,
    'entry_returned': 0x1000045c8,
    'native_clbg_entry': 0x10001afcc,
    'generic_entry_thunk': 0x100013e58,
    'initialize_runtime_state': 0x10002aa10,
    'run_original_driver': 0x10002343c,
    'energy': 0x100040fe0,
    'nbody': 0x10002a310,
    'nbody_decrement': 0x10002a9e8,
}
RUNTIME = {
    'jl_fptr_interpret_call': 0x3f1f8,
    'jl_interpret_opaque_closure': 0x3fe10,
    'jl_interpret_toplevel_thunk': 0x40054,
    'jl_interpret_toplevel_expr_in': 0x4018c,
    'jl_code_or_ci_for_interpreter': 0x3f074,
    'jl_code_for_interpreter': 0x3f1c8,
    'jl_get_abi_converter': 0xb787c,
    'jl_jit_abi_converter_fallback': 0xb76a8,
    'jl_compile_codeinst_fallback': 0xb4e2c,
    'jl_generate_fptr_for_unspecialized_fallback': 0xb4e18,
    'jl_compile_extern_c_fallback': 0xb4f48,
    'jl_init_codegen_fallback': 0xb4e08,
    'ijl_compile_method_instance': 0x1bb58,
    'jl_compile_method_internal': 0x1a130,
    'jl_read_codeinst_invoke': 0x19ffc,
}
CFUNCDATA = 0x10004c5b0
WORLD = 0x2e4c68
CFUNCDATA_FIELDS = ('fptr', 'last_world', 'plast_codeinst', 'last_codeinst',
                    'unspecialized', 'declrt', 'sigt', 'flags')
CI_FIELDS = ('def', 'owner', 'next', 'min_world', 'max_world', 'inferred',
             'flags', 'invoke', 'specptr')


def require(value, message):
    if not value:
        raise ValueError(message)


class Trace:
    """Capture bounded, raw debugger observations through an owner-provided sink.

    emit must durably save each event and enforce the prepared total byte cap.
    expected_modules maps 'main' and 'runtime' to their prepared physical path
    and UUID. Their bytes and matching DWARF/header must be pinned by the owner.
    No absence claim follows merely from successful construction or zero hits.
    """
    def __init__(self, lldb, target, modules, expected_modules, emit):
        self.lldb, self.target, self.modules, self.emit = lldb, target, modules, emit
        self.expected = expected_modules
        self.breakpoints, self.hits, self.events = {}, {}, 0
        self.finished_once = False
        self.process_identity, self.last_stop_id = None, None
        require(target.IsValid() and target.GetAddressByteSize() == 8,
                'The retained target must use 64-bit addresses')
        require(target.GetByteOrder() == lldb.eByteOrderLittle,
                'The retained target must be little endian')
        require(target.GetTriple().split('-')[0] in ('arm64', 'aarch64'),
                'The retained instruction/register plan is AArch64 only')
        self.module_inventory('before-connect')
        self.ci_type = modules['runtime'].FindFirstType('jl_code_instance_t')
        require(self.ci_type.IsValid(), 'Matching runtime CodeInstance DWARF type unavailable')
        self.ci_layout = self.layout(self.ci_type, CI_FIELDS)
        self.event('codeinstance-layout', type='jl_code_instance_t',
                   bytes=self.ci_type.GetByteSize(), fields=self.ci_layout)
        for role, addresses in (('main', MAIN), ('runtime', RUNTIME)):
            for name, file_address in addresses.items():
                address = modules[role].ResolveFileAddress(file_address)
                require(address.IsValid(), 'Unresolved file address: '+name)
                breakpoint = target.BreakpointCreateBySBAddress(address)
                require(breakpoint.IsValid() and breakpoint.GetNumLocations() == 1,
                        'Exactly one breakpoint location required: '+name)
                location = breakpoint.GetLocationAtIndex(0)
                require(location.GetAddress().GetFileAddress() == file_address,
                        'Breakpoint moved from retained file address: '+name)
                self.breakpoints[breakpoint.GetID()] = (name, role, file_address, breakpoint)
                self.hits[name] = 0
                self.event('breakpoint-installed', name=name, role=role,
                           file_address=hex(file_address), breakpoint_id=breakpoint.GetID())

    def bind_owned_process(self, process, pid, birth_identity):
        """Owner calls once, after recording birth identity and before resume."""
        require(self.process_identity is None and process.IsValid()
                and process.GetState() == self.lldb.eStateStopped,
                'Exactly one initially stopped owned process must be bound')
        require(type(pid) is int and pid > 0 and process.GetProcessID() == pid,
                'Owned process PID differs from the registered identity')
        require(isinstance(birth_identity, dict) and birth_identity,
                'Owner-provided birth identity is required')
        require(process.GetUniqueID() > 0
                and self.target.GetProcess().GetUniqueID() == process.GetUniqueID(),
                'Owned process does not belong to the prepared target')
        self.process_identity = dict(pid=pid, unique_id=process.GetUniqueID(),
                                     birth_identity=copy.deepcopy(birth_identity))
        self.event('owned-process-bound', identity=copy.deepcopy(self.process_identity),
                   initial_stop_id=process.GetStopID())

    def verify_process(self, process):
        require(self.process_identity is not None and process.IsValid()
                and process.GetProcessID() == self.process_identity['pid']
                and process.GetUniqueID() == self.process_identity['unique_id']
                and self.target.GetProcess().GetUniqueID() == process.GetUniqueID(),
                'Observation is not from the single bound target process')

    def event(self, kind, **fields):
        require(self.events < 512, 'Diagnostic event limit exceeded')
        self.events += 1
        self.emit(dict(sequence=self.events, kind=kind, **fields))

    def verify_identity(self):
        found = []
        for module in self.target.module_iter():
            spec = module.GetFileSpec()
            path = spec.fullpath
            header = module.GetObjectFileHeaderAddress()
            found.append(dict(path=path, uuid=module.GetUUIDString(),
                              file_address=hex(header.GetFileAddress()),
                              load_address=hex(header.GetLoadAddress(self.target))))
        for role, expected in self.expected.items():
            module = self.modules[role]
            require(module.GetFileSpec().fullpath == expected['path']
                    and module.GetUUIDString() == expected['uuid'],
                    'Prepared module identity differs: '+role)
            require(sum(item['path'] == expected['path'] and item['uuid'] == expected['uuid']
                        for item in found) == 1,
                    'Prepared module is missing or duplicated in the target: '+role)
        for name, role, file_address, breakpoint in self.breakpoints.values():
            require(breakpoint.IsValid() and breakpoint.IsEnabled()
                    and breakpoint.GetNumLocations() == 1,
                    'Breakpoint continuity lost: '+name)
            location = breakpoint.GetLocationAtIndex(0)
            address = location.GetAddress()
            module = address.GetModule()
            require(location.IsEnabled() and address.GetFileAddress() == file_address
                    and module.GetFileSpec().fullpath == self.expected[role]['path']
                    and module.GetUUIDString() == self.expected[role]['uuid'],
                    'Breakpoint module/address changed: '+name)
        return found

    def module_inventory(self, phase):
        self.event('module-inventory', phase=phase, modules=self.verify_identity())

    def module_event(self, event):
        """Owner feeds all target module-load/unload broadcaster events."""
        entries = []
        for index in range(self.lldb.SBTarget.GetNumModulesFromEvent(event)):
            module = self.lldb.SBTarget.GetModuleAtIndexFromEvent(index, event)
            entries.append(dict(path=module.GetFileSpec().fullpath, uuid=module.GetUUIDString()))
        self.event('module-event', event_type=event.GetType(), modules=entries)
        if event.GetType() & self.lldb.SBTarget.eBroadcastBitModulesUnloaded:
            require(not any(item['path'] == expected['path'] for item in entries
                            for expected in self.expected.values()),
                    'A prepared breakpoint-owning module was unloaded')
        self.verify_identity()

    @staticmethod
    def layout(type_, wanted):
        fields = {}
        for index in range(type_.GetNumberOfFields()):
            field = type_.GetFieldAtIndex(index)
            if field.GetName() in wanted:
                size, offset = field.GetType().GetByteSize(), field.GetOffsetInBytes()
                require(size in (1, 2, 4, 8) and offset+size <= type_.GetByteSize(),
                        'Unsupported runtime field layout')
                fields[field.GetName()] = dict(offset=offset, bytes=size,
                                              type=field.GetType().GetName())
        require(set(fields) == set(wanted), 'Required runtime fields unavailable')
        return fields

    def memory(self, process, address, size):
        require(address > 0 and 0 < size <= 4096, 'Invalid bounded memory request')
        error = self.lldb.SBError()
        raw = process.ReadMemory(address, size, error)
        require(error.Success() and len(raw) == size, 'Incomplete target memory read')
        return raw

    def load_address(self, role, file_address):
        address = self.modules[role].ResolveFileAddress(file_address)
        result = address.GetLoadAddress(self.target)
        require(result != self.lldb.LLDB_INVALID_ADDRESS, 'Prepared image is not loaded')
        return result

    def ci(self, process, pointer):
        if not pointer:
            return dict(address='0x0', present=False)
        size = self.ci_type.GetByteSize()
        raw = self.memory(process, pointer, size)
        values = {name: int.from_bytes(raw[v['offset']:v['offset']+v['bytes']], 'little')
                  for name, v in self.ci_layout.items()}
        # Preserve the tagged object header as bytes, without guessing dynamic
        # types or interpreting a non-null inferred pointer as executable IR.
        inferred = values['inferred']
        inferred_header = self.memory(process, inferred-8, 16).hex() if inferred else None
        return dict(address=hex(pointer), present=True, raw=raw.hex(),
                    fields={key: hex(value) for key, value in values.items()},
                    inferred_header_and_prefix=inferred_header,
                    serialized_ir_disposition='unreviewed')

    def dispatch(self, process):
        address = self.load_address('main', CFUNCDATA)
        raw = self.memory(process, address, 64)
        fields = dict(zip(CFUNCDATA_FIELDS, struct.unpack('<8Q', raw)))
        indirect_ci = (int.from_bytes(self.memory(process, fields['plast_codeinst'], 8), 'little')
                       if fields['plast_codeinst'] else 0)
        pointers = sorted({fields['last_codeinst'], indirect_ci}-{0})
        return dict(address=hex(address), raw=raw.hex(),
                    fields={key: hex(value) for key, value in fields.items()},
                    world=int.from_bytes(self.memory(process, self.load_address('runtime', WORLD), 8), 'little'),
                    selected_codeinstances=[self.ci(process, pointer) for pointer in pointers])

    def stopped(self, process):
        self.verify_process(process)
        require(process.IsValid() and process.GetState() == self.lldb.eStateStopped,
                'A stopped owned process is required')
        stop_id = process.GetStopID()
        require(self.last_stop_id is None or stop_id > self.last_stop_id,
                'Duplicate or out-of-order process stop')
        self.last_stop_id = stop_id
        self.verify_identity()
        observed = False
        for thread in process:
            reason = thread.GetStopReason()
            if reason in (self.lldb.eStopReasonNone, self.lldb.eStopReasonInvalid):
                continue
            require(reason == self.lldb.eStopReasonBreakpoint,
                    'Unexpected stop reason: '+str(reason))
            count = thread.GetStopReasonDataCount()
            require(count > 0 and count % 2 == 0, 'Malformed breakpoint stop')
            frame = thread.GetFrameAtIndex(0)
            for index in range(0, count, 2):
                identifier = thread.GetStopReasonDataAtIndex(index)
                require(identifier in self.breakpoints, 'Unregistered breakpoint stop')
                name, role, file_address, bp = self.breakpoints[identifier]
                require(frame.GetPC() == self.load_address(role, file_address),
                        'Stopped PC differs from the retained instruction')
                self.hits[name] += 1
                require(self.hits[name] <= 64, 'Per-breakpoint event limit exceeded')
                registers = {}
                for register in ('x0', 'x1', 'x8', 'x9', 'x10', 'x13', 'lr'):
                    value = frame.FindRegister(register)
                    require(value.IsValid() and value.GetError().Success(), 'Missing register '+register)
                    registers[register] = hex(value.GetValueAsUnsigned())
                stack = [dict(pc=hex(thread.GetFrameAtIndex(i).GetPC()),
                              function=thread.GetFrameAtIndex(i).GetFunctionName())
                         for i in range(min(thread.GetNumFrames(), 12))]
                detail = self.dispatch(process) if name in (
                    'entry_world_compare', 'entry_indirect_call', 'entry_returned') else None
                self.event('breakpoint-stop', name=name, thread_id=thread.GetThreadID(),
                           stop_id=stop_id, process_unique_id=process.GetUniqueID(),
                           pc=hex(frame.GetPC()), registers=registers, stack=stack,
                           dispatch=detail)
                observed = True
        require(observed, 'No registered breakpoint caused this stop')

    def finished(self, process):
        self.verify_process(process)
        require(not self.finished_once and process.GetState() == self.lldb.eStateExited,
                'Exactly one normally exited owned process is required')
        self.finished_once = True
        self.module_inventory('exited')
        for name, role, address, breakpoint in self.breakpoints.values():
            require(breakpoint.GetNumLocations() == 1,
                    'Breakpoint resolution changed: '+name)
        self.event('capture-ended', pid=process.GetProcessID(), exit_status=process.GetExitStatus(),
                   observed_hits=dict(self.hits), native_owner_qualified=False,
                   actual_ir_removal_qualified=False, fallback_closure_qualified=False,
                   runtime_aot_proven=False, chart_admission=False)
