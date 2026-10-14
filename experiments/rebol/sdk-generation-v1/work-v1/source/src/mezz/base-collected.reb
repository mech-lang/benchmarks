REBOL [
	title:    "Rebol base code collected from C sources"
	purpose:  "This is code which must be evaluated just after code from base-defs.reb file"
	commment: "AUTO-GENERATED FILE - Do not modify. (From: pre-make.r3 [make-headers])"
]
;- code from: %/private/tmp/mech-benchmark-completion/experiments/rebol/sdk-generation-v1/work-v1/source/src/core/u-bincode.c


system/standard/bincode: make object! [
	type: 'bincode
	buffer:
	buffer-write: none
	r-mask:
	w-mask: 0
]

;- code from: %/private/tmp/mech-benchmark-completion/experiments/rebol/sdk-generation-v1/work-v1/source/src/core/u-image-resize.c


	append system/catalog [
		filters [
		  Point
		  Box
		  Triangle
		  Hermite
		  Hanning
		  Hamming
		  Blackman
		  Gaussian
		  Quadratic
		  Cubic
		  Catrom
		  Mitchell
		  Lanczos
		  Bessel
		  Sinc
		]
	]

;- code from: %/private/tmp/mech-benchmark-completion/experiments/rebol/sdk-generation-v1/work-v1/source/src/core/u-qoi.c


	if find system/codecs 'qoi [
		system/codecs/qoi/title: "Quite OK Image"
		system/codecs/qoi/type: 'image
		system/codecs/qoi/suffixes: [%.qoi]
		append append system/catalog/file-types system/codecs/qoi/suffixes 'qoi
	]
