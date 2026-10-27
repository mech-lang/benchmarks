use std::sync::Arc;

use mech_core::{
    FunctionCatalog,
    FunctionCatalogBuilder,
    MResult,
};

pub fn function_catalog() -> MResult<Arc<FunctionCatalog>> {
    let mut builder = FunctionCatalogBuilder::new();

    mech_engine::install_intrinsic_resident(
        &mut builder,
    )?;

    Ok(Arc::new(builder.build()?))
}
