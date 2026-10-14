package boundedqualification;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.PrintStream;
import java.lang.management.GarbageCollectorMXBean;
import java.lang.management.ManagementFactory;
import java.lang.ref.Reference;
import java.lang.ref.WeakReference;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import javax.management.MBeanServer;
import javax.management.ObjectName;

/** Bounded diagnostics of unchanged scored methods; no subject compilation. */
public final class WorkProbe {
  static volatile Object pressureSink;
  static final int[] LENGTHS = {1, 2, 3, 4, 6, 12, 18};
  static void require(boolean value, String message) { BoundedProbe.require(value, message); }
  static Object call(Method method, Object... args) throws Throwable {
    try { return method.invoke(null, args); }
    catch (InvocationTargetException error) { throw error.getCause(); }
  }
  static String digest(byte[] bytes) throws Exception {
    return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
  }
  static void json(Path path, Object value) throws Exception {
    Files.writeString(path, BoundedProbe.json(value) + "\n", StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
  }
  static long collections() {
    long count = 0;
    for (GarbageCollectorMXBean gc : ManagementFactory.getGarbageCollectorMXBeans()) {
      require(gc.getName().startsWith("G1 "), "Expected only original G1 collectors");
      if (gc.getCollectionCount() >= 0) count += gc.getCollectionCount();
    }
    return count;
  }

  static void graph(Object node, int depth, Method left, Method right,
                    IdentityHashMap<Object,Boolean> seen, List<WeakReference<Object>> weak) throws Throwable {
    require(node != null && seen.put(node, Boolean.TRUE) == null, "Missing or shared scored tree node");
    if (weak != null) weak.add(new WeakReference<>(node));
    Object a = left.invoke(node), b = right.invoke(node);
    if (depth == 0) require(a == null && b == null, "Scored leaf has children");
    else {
      require(a != null && b != null && a != b, "Scored branch is incomplete or aliased");
      graph(a, depth - 1, left, right, seen, weak);
      graph(b, depth - 1, left, right, seen, weak);
    }
  }

  static List<Object> freshness(Class<?> type, Class<?> node) throws Throwable {
    Method tree = type.getMethod("tree", int.class), check = type.getMethod("check", node);
    Method left = node.getMethod("getLeft"), right = node.getMethod("getRight");
    IdentityHashMap<Object,Boolean> all = new IdentityHashMap<>();
    List<Object> cases = new ArrayList<>();
    for (int depth : new int[] {0, 1, 4, 6, 8}) {
      int wanted = (1 << (depth + 1)) - 1;
      for (int repetition = 0; repetition < 2; repetition++) {
        Object root = call(tree, depth);
        int before = all.size();
        graph(root, depth, left, right, all, null);
        require(all.size() - before == wanted, "Wrong complete scored node count");
        require(call(check, root).equals((long)wanted), "Scored check differs from inspected graph");
        cases.add(Map.of("depth", depth, "repetition", repetition, "nodes", wanted));
      }
    }
    // This method returns no strong reference to a scored tree or descendant.
    return cases;
  }

  static List<WeakReference<Object>> weakGraph(Object root, int depth, Method left, Method right) throws Throwable {
    List<WeakReference<Object>> weak = new ArrayList<>();
    graph(root, depth, left, right, new IdentityHashMap<>(), weak);
    return weak;
  }

  static Map<String,Object> trees(Class<?> type, ClassLoader loader) throws Throwable {
    Class<?> node = Class.forName("clbg.binarytrees.Node", false, loader);
    List<Object> fresh = freshness(type, node);
    Method tree = type.getMethod("tree", int.class), check = type.getMethod("check", node);
    Method left = node.getMethod("getLeft"), right = node.getMethod("getRight");
    Object root = call(tree, 8);
    List<WeakReference<Object>> before = weakGraph(root, 8, left, right);
    long gcBefore = collections(), started = System.nanoTime();
    byte[][] pressure = new byte[32][];
    int allocated = 0;
    while (allocated < 256 && System.nanoTime() - started < 5_000_000_000L && collections() == gcBefore) {
      int index = allocated % pressure.length;
      pressure[index] = null;
      pressure[index] = new byte[1024 * 1024];
      pressure[index][0] = (byte)allocated;
      pressureSink = pressure;
      allocated++;
    }
    long gcAfter = collections();
    List<WeakReference<Object>> after = weakGraph(root, 8, left, right);
    require(before.size() == 511 && before.size() == after.size(), "Long-lived tree shape changed");
    for (int i = 0; i < before.size(); i++)
      require(before.get(i).get() != null && before.get(i).get() == after.get(i).get(), "Scored descendant identity changed");
    require(call(check, root).equals(511L), "Long-lived scored check changed");
    Reference.reachabilityFence(root);
    pressureSink = null;
    Map<String,Object> result = new LinkedHashMap<>();
    result.put("fresh_identity_cases", fresh);
    result.put("all_graphs_disjoint", true);
    result.put("retained_root_depth", 8);
    result.put("retained_descendants", before.size());
    result.put("only_root_strong_during_pressure", true);
    result.put("descendant_identity_preserved", true);
    result.put("gc_count_before", gcBefore); result.put("gc_count_after", gcAfter);
    result.put("normal_gc_observed", gcAfter > gcBefore);
    result.put("pressure_allocated_bytes", (long)allocated * 1024 * 1024);
    result.put("pressure_retained_bound_bytes", 32L * 1024 * 1024);
    result.put("pressure_elapsed_ns", System.nanoTime() - started);
    result.put("tree_root_requests", 11); result.put("check_root_requests", 11);
    result.put("optimized_main_allocation_and_lifetime_proved", false);
    return result;
  }

  static Map<String,Long> independentMap(String sequence, int k) {
    // Enumerate distinct observed words, then count overlapping matches by
    // indexOf. This differs from the scored one-pass per-window accumulation.
    Map<String,Long> expected = new TreeMap<>();
    for (int i = 0; i + k <= sequence.length(); i++) expected.put(sequence.substring(i, i + k), 0L);
    for (String word : expected.keySet()) {
      long count = 0;
      for (int at = sequence.indexOf(word); at >= 0; at = sequence.indexOf(word, at + 1)) count++;
      expected.put(word, count);
    }
    return expected;
  }

  static List<Object> maps(Class<?> type) throws Throwable {
    String seed = "GGTATTTTAATTTATAGTACGTACGTTGCA";
    List<String> sequences = new ArrayList<>();
    for (int length : new int[] {0, 1, 2, 17, 18, 19}) sequences.add(seed.substring(0, length));
    sequences.add(seed + "AAAAACCCCCGGGGGTTTTT" + seed + "ACGTACGT");
    Method table = type.getMethod("table", String.class, int.class);
    List<Object> cases = new ArrayList<>();
    for (String sequence : sequences) {
      IdentityHashMap<Object,Boolean> identities = new IdentityHashMap<>();
      List<Map<?,?>> retained = new ArrayList<>();
      List<Object> rows = new ArrayList<>();
      for (int k : LENGTHS) {
        Object raw = call(table, sequence, k);
        require(raw instanceof HashMap<?,?> && identities.put(raw, Boolean.TRUE) == null, "Expected fresh full HashMap");
        Map<?,?> actual = (Map<?,?>)raw;
        Map<String,Long> expected = independentMap(sequence, k);
        require(actual.equals(expected), "Complete scored k-mer map differs at k=" + k);
        long total = 0;
        for (Object count : actual.values()) { require(count instanceof Long, "Wrong k-mer count type"); total += (Long)count; }
        require(total == Math.max(0, sequence.length() - k + 1), "Wrong complete window count");
        retained.add(actual);
        rows.add(Map.of("k", k, "entries", expected, "count_sum", total));
      }
      Object repeated = call(table, sequence, 3);
      require(identities.put(repeated, Boolean.TRUE) == null && repeated.equals(independentMap(sequence, 3)), "Repeated table is not fresh/correct");
      for (int i = 0; i < LENGTHS.length; i++)
        require(retained.get(i).equals(independentMap(sequence, LENGTHS[i])), "Retained map mutated after another table call");
      require(retained.size() == 7, "All seven maps must remain live simultaneously");
      Reference.reachabilityFence(retained);
      cases.add(Map.of("sequence", sequence, "length", sequence.length(), "maps", rows,
          "seven_distinct_simultaneously_retained", true, "repeat_is_fresh", true,
          "earlier_maps_unchanged", true, "table_invocations", 8));
    }
    return cases;
  }

  static List<Object> copiedPermutation(Class<?> type) throws Throwable {
    Method flips = type.getMethod("flips", int[].class);
    List<Object> cases = new ArrayList<>();
    for (int[] input : new int[][] {{0}, {1, 0}, {2, 0, 1}, {3, 2, 1, 0}, {1, 3, 0, 2}}) {
      int[] before = input.clone(), expectedWork = input.clone();
      int expected = 0;
      while (expectedWork[0] != 0) {
        int[] prefix = Arrays.copyOf(expectedWork, expectedWork[0] + 1);
        for (int i = 0; i < prefix.length; i++) expectedWork[i] = prefix[prefix.length - 1 - i];
        expected++;
      }
      require(call(flips, (Object)input).equals(expected) && Arrays.equals(input, before), "Scored flips changed source permutation");
      List<Integer> values = new ArrayList<>(); for (int value : before) values.add(value);
      cases.add(Map.of("permutation", values, "flips", expected, "original_unchanged", true));
    }
    return cases;
  }

  static void checkOutput(String benchmark, byte[] actual, byte[] expected) {
    if (!benchmark.equals("nbody")) { require(Arrays.equals(actual, expected), "Complete diagnostic main output differs"); return; }
    String output = new String(actual, StandardCharsets.US_ASCII);
    require(output.matches("-?[0-9]+\\.[0-9]{9}\\n-?[0-9]+\\.[0-9]{9}\\n"), "Malformed N-body output");
    String[] a = output.split("\\n"), b = new String(expected, StandardCharsets.US_ASCII).split("\\n");
    require(b.length == 2, "Wrong N-body reference");
    for (int i = 0; i < 2; i++) {
      double x = Double.parseDouble(a[i]), y = Double.parseDouble(b[i]);
      require(Double.isFinite(x) && Double.isFinite(y) && Math.abs(x - y) <= 1e-8, "N-body diagnostic energy differs");
    }
  }

  public static void main(String[] args) throws Throwable {
    require(args.length == 10, "Expected classes, stdlib, owners, benchmark, stdin, expected, n, output, repetitions, milliseconds");
    Path output = Path.of(args[7]).toRealPath();
    Map<String,Object> report = new LinkedHashMap<>();
    report.put("status", "failed"); report.put("main_invocations", 0); report.put("main_returns", 0);
    report.put("benchmark", args[3]); report.put("benchmark_samples", 0);
    report.put("source_work_qualified", false); report.put("optimized_main_allocation_and_lifetime_proved", false);
    Throwable failure = null;
    BoundedProbe.SubjectLoader loader = null;
    InputStream savedInput = System.in; PrintStream savedOutput = System.out;
    Thread thread = Thread.currentThread(); ClassLoader savedContext = thread.getContextClassLoader();
    try {
      Map<String,Object> runtime = BoundedProbe.runtime();
      runtime.put("JVM_MAIN", WorkProbe.class.getName());
      report.put("runtime", runtime);
      report.put("probe_owner", WorkProbe.class.getName());
      report.put("probe_code_source", WorkProbe.class.getProtectionDomain().getCodeSource().getLocation().toExternalForm());
      Path classes = Path.of(args[0]).toRealPath(), stdlib = Path.of(args[1]).toRealPath();
      Set<String> owners = BoundedProbe.readOwners(Path.of(args[2]));
      BoundedProbe.verifyInventory(classes, owners);
      loader = new BoundedProbe.SubjectLoader(classes, stdlib, owners);
      thread.setContextClassLoader(loader);
      try { Class.forName("clbg.UnexpectedOwner", false, loader); throw new AssertionError("Unknown owner loaded"); }
      catch (ClassNotFoundException expected) { report.put("denied_owner_canary", true); }
      String mainOwner = "clbg." + args[3] + ".MainKt";
      Class<?> type = Class.forName(mainOwner, true, loader);
      report.put("main_owner", mainOwner); report.put("subject_owner_names", new ArrayList<>(owners));
      report.put("main_code_source", type.getProtectionDomain().getCodeSource().getLocation().toExternalForm());
      if (args[3].equals("binarytrees")) report.put("tree_witness", trees(type, loader));
      if (args[3].equals("knucleotide")) report.put("map_witness", maps(type));
      if (args[3].equals("fannkuchredux")) report.put("copy_witness", copiedPermutation(type));
      Method main = type.getDeclaredMethod("main", String[].class);
      require(Modifier.isPublic(main.getModifiers()) && Modifier.isStatic(main.getModifiers()) &&
          main.getReturnType() == void.class && main.getDeclaringClass() == type, "Wrong scored main signature");
      byte[] payload = Files.readAllBytes(Path.of(args[4])), expected = Files.readAllBytes(Path.of(args[5]));
      int repetitions = Integer.parseInt(args[8]), milliseconds = Integer.parseInt(args[9]);
      require(repetitions == 10000 && milliseconds == 20000, "Unreviewed warmup bound");
      MessageDigest transcript = MessageDigest.getInstance("SHA-256");
      long started = System.nanoTime(); byte[] last = null; int count = 0;
      while (count < repetitions && System.nanoTime() - started < milliseconds * 1_000_000L) {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        PrintStream captured = new PrintStream(bytes, true, StandardCharsets.ISO_8859_1);
        System.setIn(new ByteArrayInputStream(payload)); System.setOut(captured);
        report.put("main_invocations", count + 1);
        call(main, (Object)new String[] {args[6]});
        report.put("main_returns", count + 1);
        captured.flush(); byte[] actual = bytes.toByteArray();
        require(actual.length <= 1024 * 1024, "Diagnostic main stdout exceeded bound");
        checkOutput(args[3], actual, expected);
        if (count == 0) Files.write(output.resolve("first.stdout"), actual, StandardOpenOption.CREATE_NEW);
        last = actual; transcript.update(actual); count++;
        captured.close();
      }
      System.setIn(savedInput); System.setOut(savedOutput);
      require(count > 0, "No scored main invocation completed");
      Files.write(output.resolve("last.stdout"), last, StandardOpenOption.CREATE_NEW);
      report.put("main_output_checks", count); report.put("main_argument", args[6]);
      report.put("main_stdout_transcript_sha256", HexFormat.of().formatHex(transcript.digest()));
      report.put("stdin_sha256", digest(payload)); report.put("expected_stdout_sha256", digest(expected));
      report.put("warmup_elapsed_ns", System.nanoTime() - started);
      report.put("maximum_main_invocations", repetitions); report.put("warmup_deadline_milliseconds", milliseconds);
      MBeanServer server = ManagementFactory.getPlatformMBeanServer();
      ObjectName diagnostic = new ObjectName("com.sun.management:type=DiagnosticCommand");
      String libraries = (String)server.invoke(diagnostic, "vmDynlibs", new Object[0], new String[0]);
      Files.writeString(output.resolve("native-libraries.txt"), libraries, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
      report.put("native_library_inventory", "DiagnosticCommand.vmDynlibs");
      report.put("status", "work-witnesses-recorded");
    } catch (Throwable error) { failure = error; }
    finally {
      try { System.setIn(savedInput); System.setOut(savedOutput); thread.setContextClassLoader(savedContext); }
      catch (Throwable error) { if (failure == null) failure = error; else failure.addSuppressed(error); }
      if (loader != null) {
        loader.record(report);
        try { loader.close(); }
        catch (Throwable error) { if (failure == null) failure = error; else failure.addSuppressed(error); }
      }
      if (failure != null) {
        report.put("status", "failed"); report.put("error_type", failure.getClass().getName());
        report.put("error", failure.getMessage());
      }
      try { json(output.resolve("summary.json"), report); }
      catch (Throwable error) { if (failure == null) failure = error; else failure.addSuppressed(error); }
    }
    if (failure != null) throw failure;
  }
}
