use cranelift_codegen::ir::{InstBuilder, Value, types, condcodes::IntCC};
use cranelift_frontend::FunctionBuilder;
type NativeCompileError = String;
fn backend(error: &str) -> String { error.to_owned() }
fn linear_ordinal(
    b: &mut FunctionBuilder<'_>,
    ordinal: Value,
    rows: Value,
    columns: Value,
    schema: &mech_core::SchemaBody,
) -> Value {
    // The same entry witness that lends this view has already checked the
    // current owner's exact schema and dimensions. A unit dimension makes
    // column-major source order identical to row-major backing order. Derive
    // this immutable fact from that witness, never from a previous view.
    let vector = matches!(schema, mech_core::SchemaBody::Matrix { dimensions, .. }
        if dimensions.len() == 2 && dimensions.iter().any(|dimension|
            matches!(dimension, mech_core::DimensionExpr::Constant(1))));
    if vector {
        ordinal
    } else {
        // Generic schemas can still carry a current row or column vector.
        // The caller has checked this admitted view's bounds, so either unit
        // dimension makes the physical ordinal identical to source order.
        let one_row = b.ins().icmp_imm(IntCC::Equal, rows, 1);
        let one_column = b.ins().icmp_imm(IntCC::Equal, columns, 1);
        let contiguous = b.ins().bor(one_row, one_column);
        let general = b.create_block();
        let done = b.create_block();
        b.append_block_param(done, types::I64);
        b.ins()
            .brif(contiguous, done, &[ordinal.into()], general, &[]);
        b.switch_to_block(general);
        let column = b.ins().udiv(ordinal, rows);
        // Bounds on the admitted view prove rows > 0. Reuse the quotient:
        // column * rows <= ordinal, so this internal remainder cannot overflow.
        // Separate urem/udiv lower to duplicate machine divisions on AArch64.
        let consumed = b.ins().imul(column, rows);
        let row = b.ins().isub(ordinal, consumed);
        let row = b.ins().imul(row, columns);
        let physical = b.ins().iadd(row, column);
        b.ins().jump(done, &[physical.into()]);
        b.switch_to_block(done);
        b.block_params(done)[0]
    }
}

/// Canonical linear selection is column-major over row-major physical storage.
/// Call only after the admitted unsigned view and one-based bounds check.
fn linear_address(
    b: &mut FunctionBuilder<'_>,
    ordinal: Value,
    rows: Value,
    columns: Value,
    width: u8,
    schema: &mech_core::SchemaBody,
    base: impl FnOnce(&mut FunctionBuilder<'_>) -> Value,
) -> Result<(Value, cranelift_codegen::ir::Type), NativeCompileError> {
    let physical = linear_ordinal(b, ordinal, rows, columns, schema);
    element_address(b, physical, width, base)
}

/// Address an already translated physical element ordinal. A guarded vector
/// entry may supply its logical ordinal directly: for either unit dimension,
/// canonical source order and backing order are identical. Bounds still precede
/// this operation, and packed element width remains independent of geometry.
fn element_address(
    b: &mut FunctionBuilder<'_>,
    physical: Value,
    width: u8,
    base: impl FnOnce(&mut FunctionBuilder<'_>) -> Value,
) -> Result<(Value, cranelift_codegen::ir::Type), NativeCompileError> {
    let at = b.ins().imul_imm(physical, i64::from(width));
    let base = base(b);
    let address = b.ins().iadd(base, at);
    let ty = match width {
        1 => types::I8,
        2 => types::I16,
        4 => types::I32,
        8 => types::I64,
        _ => return Err(backend("numeric load width differs")),
    };
    Ok((address, ty))
}


mod tests {
use super::linear_address;
use cranelift_codegen::ir::{AbiParam, Function, InstBuilder, Opcode, types};
use cranelift_frontend::{FunctionBuilder, FunctionBuilderContext};
use mech_core::{DimensionExpr as Dim, DimensionParameterId, IntegerWidth, SchemaBody};

fn address_function(schema: &SchemaBody, width: u8) -> Function {
    let mut function = Function::new();
    function.signature.params = vec![AbiParam::new(types::I64); 4];
    function.signature.returns = vec![AbiParam::new(types::I64)];
    let mut context = FunctionBuilderContext::new();
    {
        let mut builder = FunctionBuilder::new(&mut function, &mut context);
        let entry = builder.create_block();
        builder.append_block_params_for_function_params(entry);
        builder.switch_to_block(entry);
        let args = builder.block_params(entry).to_vec();
        let (address, _) = linear_address(
            &mut builder,
            args[0],
            args[1],
            args[2],
            width,
            schema,
            |_| args[3],
        )
        .unwrap();
        builder.ins().return_(&[address]);
        builder.seal_all_blocks();
        builder.finalize();
    }
    function
}

fn general_schema(width: u8) -> SchemaBody {
    SchemaBody::Matrix {
        element: Box::new(SchemaBody::UnsignedInteger(match width {
            1 => IntegerWidth::W8,
            2 => IntegerWidth::W16,
            4 => IntegerWidth::W32,
            8 => IntegerWidth::W64,
            _ => unreachable!(),
        })),
        dimensions: Box::new([
            Dim::Parameter(DimensionParameterId::new(0)),
            Dim::Parameter(DimensionParameterId::new(1)),
        ]),
    }
}

type Address = unsafe extern "C" fn(u64, u64, u64, u64) -> u64;

fn native_address(width: u8) -> (cranelift_jit::JITModule, Address, String) {
    use cranelift_module::{Linkage, Module, default_libcall_names};
    let mut module = cranelift_jit::JITModule::new(
        cranelift_jit::JITBuilder::with_flags(&[("opt_level", "speed")], default_libcall_names())
            .unwrap(),
    );
    let mut context = module.make_context();
    context.func = address_function(&general_schema(width), width);
    context.func.signature.call_conv = module.make_signature().call_conv;
    context.set_disasm(true);
    let id = module
        .declare_function("numeric_address", Linkage::Local, &context.func.signature)
        .unwrap();
    module.define_function(id, &mut context).unwrap();
    let assembly = context.compiled_code().unwrap().vcode.clone().unwrap();
    module.finalize_definitions().unwrap();
    // SAFETY: the owned generated function has exactly four word arguments
    // and one word result. It computes an address without dereferencing it.
    let address: Address = unsafe { core::mem::transmute(module.get_finalized_function(id)) };
    (module, address, assembly)
}

#[test]
fn general_numeric_addresses_emit_one_machine_division() {
    for width in [1, 2, 4, 8] {
        let (_module, _, assembly) = native_address(width);
        if cfg!(target_arch = "aarch64") {
            let divisions = assembly
                .lines()
                .filter(|line| line.contains("udiv "))
                .count();
            assert_eq!(divisions, 1, "width={width}\n{assembly}");
        }
        let function = address_function(&general_schema(width), width);
        let divisions = function
            .layout
            .blocks()
            .flat_map(|block| function.layout.block_insts(block))
            .filter(|&inst| {
                matches!(
                    function.dfg.insts[inst].opcode(),
                    Opcode::Udiv | Opcode::Urem
                )
            })
            .count();
        assert_eq!(divisions, 1, "width={width}\n{}", function.display());
    }
}

}
