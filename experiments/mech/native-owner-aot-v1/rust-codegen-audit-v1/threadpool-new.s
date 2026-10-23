; /usr/bin/otool -tvV /private/tmp/mech-benchmark-publication/experiments/mech/native-hashmap-work-v1/.build/knucleotide-rust-7
; Address range [0x10000f7e0, 0x10000f884)
000000010000f7e0	sub	sp, sp, #0xc0
000000010000f7e4	stp	x20, x19, [sp, #0xa0]
000000010000f7e8	stp	x29, x30, [sp, #0xb0]
000000010000f7ec	add	x29, sp, #0xb0
000000010000f7f0	bl	__RNvCsigvcXpkSleP_8num_cpus12get_num_cpus
000000010000f7f4	cmp	x0, #0x1
000000010000f7f8	mov	x8, #-0x8000000000000000
000000010000f7fc	str	xzr, [sp, #0x8]
000000010000f800	str	x8, [sp, #0x18]
000000010000f804	csinc	x8, x0, xzr, hi
000000010000f808	mov	w9, #0xca00
000000010000f80c	movk	w9, #0x3b9a, lsl #16
000000010000f810	str	w9, [sp, #0x38]
000000010000f814	str	xzr, [sp, #0x40]
000000010000f818	str	xzr, [sp, #0x50]
000000010000f81c	str	xzr, [sp, #0x60]
000000010000f820	str	xzr, [sp, #0x70]
000000010000f824	mov	w9, #0x64
000000010000f828	stp	x8, x9, [sp, #0x90]
000000010000f82c	mov	w8, #0x1
000000010000f830	adrp	x9, 97 ; 0x100070000
000000010000f834	add	x9, x9, #0xef8
000000010000f838	stp	x8, x9, [sp, #0x80]
000000010000f83c	add	x0, sp, #0x8
000000010000f840	bl	__RNvMNtCs5EI0rDwdvyU_16tokio_threadpool7builderNtB2_7Builder5build
000000010000f844	mov	x19, x0
000000010000f848	mov	x20, x1
000000010000f84c	add	x0, sp, #0x8
000000010000f850	bl	__RINvNtCsgDHHaSskbIF_4core3ptr13drop_in_placeNtNtCs5EI0rDwdvyU_16tokio_threadpool7builder7BuilderEBK_
000000010000f854	mov	x0, x19
000000010000f858	mov	x1, x20
000000010000f85c	ldp	x29, x30, [sp, #0xb0]
000000010000f860	ldp	x20, x19, [sp, #0xa0]
000000010000f864	add	sp, sp, #0xc0
000000010000f868	ret
000000010000f86c	mov	x19, x0
000000010000f870	add	x0, sp, #0x8
000000010000f874	bl	__RINvNtCsgDHHaSskbIF_4core3ptr13drop_in_placeNtNtCs5EI0rDwdvyU_16tokio_threadpool7builder7BuilderEBK_
000000010000f878	mov	x0, x19
000000010000f87c	bl	0x1000556b8 ; symbol stub for: __Unwind_Resume
000000010000f880	bl	__RNvNtCsgDHHaSskbIF_4core9panicking16panic_in_cleanup
