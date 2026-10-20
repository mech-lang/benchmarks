require 'json'

# Diagnostic only: inspect after the unchanged benchmark has finished.
at_exit do
  info = {yjit: RubyVM::YJIT.enabled?, zjit: RubyVM::ZJIT.enabled?}
  begin
    kernel = method(ENV.fetch('RUBY_POLICY_KERNEL').to_sym)
    info[:kernel_source_location] = kernel.source_location
    if info[:yjit]
      disassembly = RubyVM::YJIT.disasm(kernel)
      info[:yjit_disassembly_present] = !disassembly.nil? && !disassembly.empty?
      File.write(ENV.fetch('RUBY_POLICY_REPORT') + '.disasm.txt', disassembly) if disassembly
    end
  rescue Exception => error
    info[:inspection_error] = "#{error.class}: #{error.message}"
  end
  File.write(ENV.fetch('RUBY_POLICY_REPORT'), JSON.pretty_generate(info) + "\n")
end
