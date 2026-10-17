import Std

-- The dynamic serial prevents shared constant leaves and identical child trees.
inductive Tree where
  | nil
  | node (serial : UInt64) (left right : Tree)
  deriving Inhabited

@[noinline] def makeTree : Nat → UInt64 → Tree
  | 0, serial => .node serial .nil .nil
  | depth + 1, serial =>
    .node serial (makeTree depth (2 * serial)) (makeTree depth (2 * serial + 1))

@[noinline] def checkTree : Tree → Nat
  | .nil => 0
  | .node _ left right => 1 + checkTree left + checkTree right

@[noinline] def manyTrees (depth count : Nat) : Nat := Id.run do
  let mut total := 0
  for i in [:count] do
    total := total + checkTree (makeTree depth i.toUInt64)
  return total

def main (args : List String) : IO Unit := do
  let maximum := max 6 ((args.headD "0").toNat!)
  let stretch := maximum + 1
  IO.println s!"stretch tree of depth {stretch}\t check: {checkTree (makeTree stretch 1)}"
  let long := makeTree maximum 1
  let mut tasks := #[]
  for depth in [4:maximum + 1:2] do
    let count := 2 ^ (maximum - depth + 4)
    let task := Task.spawn fun _ => manyTrees depth count
    tasks := tasks.push (count, depth, task)
  for (count, depth, task) in tasks do
    IO.println s!"{count}\t trees of depth {depth}\t check: {task.get}"
  IO.println s!"long lived tree of depth {maximum}\t check: {checkTree long}"
  (← IO.getStdout).flush
