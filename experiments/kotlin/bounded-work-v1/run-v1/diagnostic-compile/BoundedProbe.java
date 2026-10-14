package boundedqualification;

import java.io.IOException;
import java.lang.management.CompilationMXBean;
import java.lang.management.GarbageCollectorMXBean;
import java.lang.management.ManagementFactory;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Stream;

/** Unscored retained-main probe. It never reads stdin or writes stdout itself. */
public final class BoundedProbe {
  private static final String DENIED_CANARY = "clbg.UnexpectedOwner";

  static final class SubjectLoader extends URLClassLoader {
    final URL classes;
    final URL stdlib;
    final Set<String> owners;
    final Map<String,String> origins = new LinkedHashMap<>();
    final Map<String,String> resources = new LinkedHashMap<>();
    final List<String> denied = new ArrayList<>();

    SubjectLoader(Path classes, Path stdlib, Set<String> owners) throws IOException {
      super(new URL[] {classes.toUri().toURL(), stdlib.toUri().toURL()},
            ClassLoader.getPlatformClassLoader());
      this.classes = classes.toUri().toURL();
      this.stdlib = stdlib.toUri().toURL();
      this.owners = new LinkedHashSet<>(owners);
    }

    @Override protected synchronized Class<?> loadClass(String name, boolean resolve)
        throws ClassNotFoundException {
      if (name.startsWith("clbg.") && !owners.contains(name)) {
        denied.add(name);
        throw new ClassNotFoundException("Unexpected subject owner: " + name);
      }
      Class<?> loaded = findLoadedClass(name);
      if (loaded == null) {
        if (owners.contains(name) || name.startsWith("kotlin.")) {
          loaded = findClass(name);
        } else {
          try {
            loaded = getParent().loadClass(name);
          } catch (ClassNotFoundException error) {
            denied.add(name);
            throw new ClassNotFoundException("Unexpected non-platform owner: " + name, error);
          }
        }
      }
      if (resolve) resolveClass(loaded);
      return loaded;
    }

    URL expectedResource(String name) throws IOException {
      String relative = name.replace('.', '/') + ".class";
      return owners.contains(name) ? new URL(classes, relative)
          : new URL("jar:" + stdlib.toExternalForm() + "!/" + relative);
    }

    URL checkedResource(String name) throws IOException {
      URL expected = expectedResource(name);
      URL actual = findResource(name.replace('.', '/') + ".class");
      require(actual != null && actual.toExternalForm().equals(expected.toExternalForm()),
          "Unexpected class resource: " + name + " " + actual + " != " + expected);
      return actual;
    }

    @Override protected synchronized Class<?> findClass(String name) throws ClassNotFoundException {
      if (!owners.contains(name) && !name.startsWith("kotlin.")) {
        denied.add(name);
        throw new ClassNotFoundException("Unexpected non-platform owner: " + name);
      }
      try {
        URL resource = checkedResource(name);
        Class<?> found = super.findClass(name);
        require(found.getClassLoader() == this, "Unexpected defining loader: " + name);
        URL source = found.getProtectionDomain().getCodeSource().getLocation();
        URL expected = owners.contains(name) ? classes : stdlib;
        require(source.toExternalForm().equals(expected.toExternalForm()),
            "Unexpected class origin: " + name + " " + source + " != " + expected);
        origins.put(name, source.toExternalForm());
        resources.put(name, resource.toExternalForm());
        return found;
      } catch (IOException error) {
        throw new ClassNotFoundException("Cannot inspect class resource: " + name, error);
      }
    }

    synchronized void record(Map<String,Object> report) {
      report.put("non_platform_class_origins", new LinkedHashMap<>(origins));
      report.put("non_platform_class_resources", new LinkedHashMap<>(resources));
      report.put("denied_owners", new ArrayList<>(denied));
    }
  }

  static void require(boolean value, String message) {
    if (!value) throw new AssertionError(message);
  }

  static Set<String> readOwners(Path file) throws IOException {
    Set<String> owners = new LinkedHashSet<>();
    int lineNumber = 0;
    for (String name : Files.readAllLines(file, StandardCharsets.UTF_8)) {
      lineNumber++;
      require(name.matches("clbg\\.[A-Za-z_$][A-Za-z0-9_$]*(\\.[A-Za-z_$][A-Za-z0-9_$]*)*"),
          "Invalid binary owner name at line " + lineNumber + ": " + name);
      require(owners.add(name), "Duplicate binary owner: " + name);
    }
    require(!owners.isEmpty(), "Owner inventory is empty");
    require(!owners.contains(DENIED_CANARY), "Owner inventory contains the denied canary");
    return owners;
  }

  static void verifyInventory(Path classes, Set<String> expected) throws IOException {
    Set<String> actual = new LinkedHashSet<>();
    try (Stream<Path> paths = Files.walk(classes)) {
      Iterator<Path> iterator = paths.iterator();
      while (iterator.hasNext()) {
        Path file = iterator.next();
        if (!file.toString().endsWith(".class")) continue;
        require(Files.isRegularFile(file), "Class path is not a regular file: " + file);
        require(file.toRealPath().startsWith(classes), "Class path escapes retained directory: " + file);
        String relative = classes.relativize(file).toString().replace(file.getFileSystem().getSeparator(), "/");
        actual.add(relative.substring(0, relative.length() - ".class".length()).replace('/', '.'));
      }
    }
    require(actual.equals(expected), "Retained class inventory differs: actual=" + actual + " expected=" + expected);
  }

  static String json(Object value) {
    if (value == null) return "null";
    if (value instanceof String) {
      StringBuilder out = new StringBuilder("\"");
      for (char c : ((String)value).toCharArray()) {
        if (c == '"' || c == '\\') out.append('\\').append(c);
        else if (c < 32 || Character.isSurrogate(c)) out.append(String.format("\\u%04x", (int)c));
        else out.append(c);
      }
      return out.append('"').toString();
    }
    if (value instanceof Number || value instanceof Boolean) return value.toString();
    if (value instanceof Map<?,?>) {
      List<String> entries = new ArrayList<>();
      for (Map.Entry<?,?> entry : ((Map<?,?>)value).entrySet())
        entries.add(json(entry.getKey().toString()) + ":" + json(entry.getValue()));
      return "{" + String.join(",", entries) + "}";
    }
    if (value instanceof Iterable<?>) {
      List<String> entries = new ArrayList<>();
      for (Object item : (Iterable<?>)value) entries.add(json(item));
      return "[" + String.join(",", entries) + "]";
    }
    throw new AssertionError("Unsupported diagnostic JSON type: " + value.getClass());
  }

  static Map<String,Object> runtime() {
    Map<String,Object> result = new LinkedHashMap<>();
    String[][] properties = {{"JAVA_HOME","java.home"},{"RUNTIME_VERSION","java.runtime.version"},
      {"VENDOR","java.vendor"},{"OS_ARCH","os.arch"},{"VM_NAME","java.vm.name"},
      {"VM_INFO","java.vm.info"},{"CLASS_PATH","java.class.path"},{"FILE_ENCODING","file.encoding"},
      {"USER_HOME","user.home"},{"JAVA_TMPDIR","java.io.tmpdir"},{"JVM_COMMAND","sun.java.command"}};
    for (String[] property : properties) result.put(property[0], System.getProperty(property[1]));
    CompilationMXBean compiler = ManagementFactory.getCompilationMXBean();
    result.put("COMPILER", compiler == null ? null : compiler.getName());
    result.put("PROCESSORS", Integer.toString(Runtime.getRuntime().availableProcessors()));
    result.put("MAX_HEAP", Long.toString(Runtime.getRuntime().maxMemory()));
    result.put("JVM_MAIN", BoundedProbe.class.getName());
    result.put("flags", ManagementFactory.getRuntimeMXBean().getInputArguments());
    List<String> collectors = new ArrayList<>();
    for (GarbageCollectorMXBean gc : ManagementFactory.getGarbageCollectorMXBeans()) collectors.add(gc.getName());
    result.put("collectors", collectors);
    return result;
  }

  public static void main(String[] args) throws Throwable {
    require(args.length >= 4, "Expected classes, stdlib, owner-list, summary, main-owner, [main arguments]");
    Path summary = Path.of(args[3]).toAbsolutePath().normalize();
    Map<String,Object> report = new LinkedHashMap<>();
    report.put("status", "failed");
    report.put("benchmark_main_invocations", 0);
    report.put("benchmark_main_executions", 0);
    report.put("benchmark_main_returns", 0);
    report.put("benchmark_main_returned", false);
    report.put("main_loaded", false);
    report.put("main_initialized", false);
    report.put("non_platform_class_origins", new LinkedHashMap<String,String>());
    report.put("non_platform_class_resources", new LinkedHashMap<String,String>());
    report.put("denied_owners", new ArrayList<String>());
    SubjectLoader loader = null;
    Throwable failure = null;
    Thread thread = Thread.currentThread();
    ClassLoader previousContextLoader = thread.getContextClassLoader();
    boolean contextChanged = false;
    try {
      require(args.length >= 5, "Expected main-owner after summary");
      report.put("runtime", runtime());
      report.put("probe_code_source", BoundedProbe.class.getProtectionDomain().getCodeSource().getLocation().toExternalForm());
      report.put("probe_resource", BoundedProbe.class.getResource("BoundedProbe.class").toExternalForm());
      Path classes = Path.of(args[0]).toRealPath();
      Path stdlib = Path.of(args[1]).toRealPath();
      Path ownerFile = Path.of(args[2]).toRealPath();
      require(Files.isDirectory(classes), "Retained classes path must be a directory");
      require(Files.isRegularFile(stdlib), "Retained stdlib path must be a regular jar file");
      report.put("classes", classes.toString());
      report.put("stdlib", stdlib.toString());
      report.put("owner_list", ownerFile.toString());
      String mainOwner = args[4];
      String[] mainArguments = Arrays.copyOfRange(args, 5, args.length);
      report.put("main_owner", mainOwner);
      report.put("main_arguments", Arrays.asList(mainArguments));
      Set<String> owners = readOwners(ownerFile);
      report.put("subject_owner_names", new ArrayList<>(owners));
      verifyInventory(classes, owners);
      require(mainOwner.matches("clbg\\.[A-Za-z_$][A-Za-z0-9_$]*\\.MainKt"), "Unexpected benchmark main owner: " + mainOwner);
      require(owners.contains(mainOwner), "Main owner is absent from the retained owner list");
      loader = new SubjectLoader(classes, stdlib, owners);
      report.put("loader_urls", List.of(loader.classes.toExternalForm(), loader.stdlib.toExternalForm()));
      report.put("loader_parent", loader.getParent().getClass().getName());
      List<Object> inventory = new ArrayList<>();
      report.put("owner_inventory", inventory);
      for (String owner : owners) {
        Map<String,Object> row = new LinkedHashMap<>();
        row.put("owner", owner);
        row.put("resource", loader.checkedResource(owner).toExternalForm());
        row.put("expected_code_source", loader.classes.toExternalForm());
        inventory.add(row);
      }
      try {
        Class.forName(DENIED_CANARY, false, loader);
        throw new AssertionError("Prohibited owner loaded: " + DENIED_CANARY);
      } catch (ClassNotFoundException expected) {
        report.put("denied_owner_canary", true);
      }
      Class<?> type = Class.forName(mainOwner, false, loader);
      report.put("main_loaded", true);
      require(type.getClassLoader() == loader, "Benchmark main has the wrong defining loader");
      Method main = type.getDeclaredMethod("main", String[].class);
      require(main.getDeclaringClass() == type && Modifier.isPublic(main.getModifiers())
          && Modifier.isStatic(main.getModifiers()) && main.getReturnType() == void.class,
          "Benchmark main must declare public static void main(String[])");
      report.put("main_code_source", type.getProtectionDomain().getCodeSource().getLocation().toExternalForm());
      report.put("main_resource", loader.checkedResource(mainOwner).toExternalForm());
      report.put("main_method", main.toGenericString());
      thread.setContextClassLoader(loader);
      contextChanged = true;
      Class.forName(mainOwner, true, loader);
      report.put("main_initialized", true);
      report.put("benchmark_main_invocations", 1);
      report.put("benchmark_main_executions", 1);
      try {
        main.invoke(null, (Object)mainArguments);
      } catch (InvocationTargetException error) {
        throw error.getCause() == null ? error : error.getCause();
      }
      report.put("benchmark_main_returns", 1);
      report.put("benchmark_main_returned", true);
    } catch (Throwable error) {
      failure = error;
    } finally {
      try {
        if (contextChanged) thread.setContextClassLoader(previousContextLoader);
      } catch (Throwable error) {
        if (failure == null) failure = error;
        else failure.addSuppressed(error);
      }
      if (loader != null) {
        loader.record(report);
        try {
          loader.close();
        } catch (Throwable error) {
          if (failure == null) failure = error;
          else failure.addSuppressed(error);
        }
      }
      if (failure == null) {
        report.put("status", "passed");
      } else {
        report.put("error_type", failure.getClass().getName());
        report.put("error", failure.getMessage());
      }
      try {
        Files.writeString(summary, json(report) + "\n", StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
      } catch (Throwable error) {
        if (failure == null) failure = error;
        else failure.addSuppressed(error);
      }
    }
    if (failure != null) throw failure;
  }
}
