import process = require("node:process");

// Typed source draft; compilation, conformance, work and counts are pending.
// The Computer Language Benchmarks Game
// https://salsa.debian.org/benchmarksgame-team/benchmarksgame/
//
// Naive transliteration from Sebastien Loisel's C program
// contributed by Isaac Gouy
//

function eval_A(i: number,j: number): number { return 1.0/((i+j)*(i+j+1)/2+i+1) }

function eval_A_times_u(N: number, u: number[], Au: number[]): void
  {
    let i = 0, j = 0
    for(i=0;i<N;i++)
      {
        Au[i]=0
        for(j=0;j<N;j++) Au[i]+=eval_A(i,j)*u[j]
      }
  }

function eval_At_times_u(N: number, u: number[], Au: number[]): void
  {
    let i: number, j: number
    for(i=0;i<N;i++)
      {
        Au[i]=0
        for(j=0;j<N;j++) Au[i]+=eval_A(j,i)*u[j]
      }
  }

function eval_AtA_times_u(N: number, u: number[], AtAu: number[]): void
  { const v: number[] = [N]; eval_A_times_u(N,u,v); eval_At_times_u(N,v,AtAu) }

function main(N: number): void {
  var i = 0
  let u: number[] = [N], v: number[] = [N]
  for(i=0;i<N;i++) { u[i]=1; v[i]=0 }
  for(i=0;i<10;i++)
    {
      eval_AtA_times_u(N,u,v)
      eval_AtA_times_u(N,v,u)
    }
  let vBv = 0.0, vv = 0.0
  for(i=0;i<N;i++) { vBv += u[i]*v[i]; vv += v[i]*v[i] }
  console.log( Math.sqrt(vBv/vv).toFixed(9))
}

let n = (+process.argv.length > 2)
   ? +process.argv[2]
   : 100

main(n)
