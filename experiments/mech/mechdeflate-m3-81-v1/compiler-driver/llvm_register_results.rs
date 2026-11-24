#![allow(dead_code)]
mod native_artifact { pub mod program { pub mod llvm_backend {
mod recording { pub(super) struct Definition { pub id: cranelift_module::FuncId, pub function: cranelift_codegen::ir::Function } }
#[path = "@MECH_ROOT@/hosts/gpu/src/native_artifact/program/llvm_backend/compact_body.rs"]
mod compact_body;
mod lower { include!("@MECH_ROOT@/hosts/gpu/src/native_artifact/program/llvm_backend/lower.rs"); }
mod register_results_tests { include!("@MECH_ROOT@/hosts/gpu/src/native_artifact/program/llvm_backend/register_results_tests.rs"); }
} } }
