x = if ok, do: {1, 2}, else: {3, 4}
y = case x do {a, b} -> a + b end
{x, y}
