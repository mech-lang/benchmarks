-- Untimed general arithmetic-call instrumentation; application bytes unchanged.
local source = arg[1]
local n = arg[2]
local trace = assert(io.open(arg[3], 'w'))
local initialize = require 'c-gmp'
package.loaded['c-gmp'] = function(g, aux)
  initialize(g, aux)
  for _, name in ipairs({'mpz_tdiv_q', 'mpz_fdiv_q'}) do
    local original = g[name]
    g[name] = function(a, b, destination)
      local numerator = tostring(a)
      local denominator = tostring(b)
      local result = original(a, b, destination)
      trace:write(name, '\t', numerator, '\t', denominator, '\t', tostring(result), '\n')
      return result
    end
  end
  return g
end
local bn = require 'bn'
local original = bn.div
bn.div = function(a, b)
  local result = original(a, b)
  trace:write('bn.div\t', tostring(a), '\t', tostring(b), '\t', tostring(result), '\n')
  return result
end
arg = {[0] = source, [1] = n}
dofile(source)
trace:close()
