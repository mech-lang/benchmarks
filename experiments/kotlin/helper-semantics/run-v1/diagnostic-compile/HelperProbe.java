package helperqualification;

import java.io.IOException;
import java.lang.management.ManagementFactory;
import java.lang.management.GarbageCollectorMXBean;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Unscored reflection probe. Benchmark owners are never admitted by its loader. */
public final class HelperProbe {
  static final class SupportLoader extends URLClassLoader {
    final URL classes;
    final URL stdlib;
    final Map<String,String> origins = new LinkedHashMap<>();
    final List<String> denied = new ArrayList<>();

    SupportLoader(Path classes, Path stdlib) throws IOException {
      super(new URL[] {classes.toUri().toURL(), stdlib.toUri().toURL()}, ClassLoader.getPlatformClassLoader());
      this.classes = classes.toUri().toURL();
      this.stdlib = stdlib.toUri().toURL();
    }

    @Override protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
      if (name.startsWith("clbg.") && !name.equals("clbg.Support")) {
        denied.add(name);
        throw new ClassNotFoundException("Benchmark owner prohibited: " + name);
      }
      return super.loadClass(name, resolve);
    }

    @Override protected Class<?> findClass(String name) throws ClassNotFoundException {
      if (!name.equals("clbg.Support") && !name.startsWith("kotlin."))
        throw new ClassNotFoundException("Unexpected non-platform owner: " + name);
      Class<?> found = super.findClass(name);
      URL source = found.getProtectionDomain().getCodeSource().getLocation();
      URL expected = name.equals("clbg.Support") ? classes : stdlib;
      require(source.equals(expected), "Unexpected class origin: " + name + " " + source);
      origins.put(name, source.toExternalForm());
      return found;
    }
  }

  static void require(boolean value, String message) {
    if (!value) throw new AssertionError(message);
  }

  static Object call(Object support, String name, Class<?>[] types, Object... values) throws Throwable {
    Method method = support.getClass().getMethod(name, types);
    try { return method.invoke(support, values); }
    catch (InvocationTargetException error) { throw error.getCause(); }
  }

  static Map<String,Object> rejected(Object support, String label, String name, Class<?>[] types,
                                     String expected, Object... values) throws Throwable {
    Throwable failure = null;
    try { call(support, name, types, values); }
    catch (Throwable error) { failure = error; }
    require(failure != null && failure.getClass().getName().equals(expected), "Wrong rejection for " + label);
    Map<String,Object> result = new LinkedHashMap<>();
    result.put("case", label); result.put("exception", failure.getClass().getName());
    result.put("message", failure.getMessage());
    return result;
  }

  static String json(Object value) {
    if (value == null) return "null";
    if (value instanceof String) {
      StringBuilder out = new StringBuilder("\"");
      for (char c : ((String)value).toCharArray()) {
        if (c == '"' || c == '\\') out.append('\\').append(c);
        else if (c < 32) out.append(String.format("\\u%04x", (int)c));
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
      {"USER_HOME","user.home"},{"JAVA_TMPDIR","java.io.tmpdir"}};
    for (String[] property : properties) result.put(property[0],System.getProperty(property[1]));
    result.put("COMPILER",ManagementFactory.getCompilationMXBean().getName());
    result.put("PROCESSORS",Integer.toString(Runtime.getRuntime().availableProcessors()));
    result.put("MAX_HEAP",Long.toString(Runtime.getRuntime().maxMemory()));
    result.put("flags",ManagementFactory.getRuntimeMXBean().getInputArguments());
    List<String> collectors = new ArrayList<>();
    for (GarbageCollectorMXBean gc : ManagementFactory.getGarbageCollectorMXBeans()) collectors.add(gc.getName());
    result.put("collectors",collectors);
    return result;
  }

  public static void main(String[] args) throws Throwable {
    require(args.length == 5,"Expected classes, stdlib, vectors, summary, prohibited-main owner");
    Path classes = Path.of(args[0]).toRealPath();
    Path stdlib = Path.of(args[1]).toRealPath();
    Path summary = Path.of(args[3]);
    Map<String,Object> report = new LinkedHashMap<>();
    report.put("status","failed"); report.put("benchmark_main_executions",0);
    report.put("runtime",runtime());
    try (SupportLoader loader = new SupportLoader(classes,stdlib)) {
      try {
        for (String denied : List.of(args[4],"clbg.UnexpectedHelper")) {
          try { Class.forName(denied,false,loader); throw new AssertionError("Prohibited owner loaded"); }
          catch (ClassNotFoundException expected) { /* Negative loader canary. */ }
        }
        Class<?> type = Class.forName("clbg.Support",true,loader);
        Object support = type.getField("INSTANCE").get(null);
        report.put("support_code_source",type.getProtectionDomain().getCodeSource().getLocation().toExternalForm());
        report.put("support_resource",type.getResource("Support.class").toExternalForm());
        report.put("denied_owners",loader.denied);

        Class<?>[] sizeTypes = {String[].class,int.class};
        String[][] accepted = {{},{"0"},{"1"},{"+7"},{"0007"},{"2147483647"},{"\u0667"},{"\uff17"}};
        int[] integers = {42,0,1,7,7,Integer.MAX_VALUE,7,7};
        List<Object> acceptedRecords = new ArrayList<>();
        for (int i=0;i<accepted.length;i++) {
          Object actual = call(support,"size",sizeTypes,accepted[i],42);
          require(actual.equals(integers[i]),"Integer parsing mismatch");
          acceptedRecords.add(Map.of("arguments",Arrays.asList(accepted[i]),"fallback",42,"result",actual));
        }
        report.put("integer_accepted",acceptedRecords);
        List<Object> rejectedRecords = new ArrayList<>();
        rejectedRecords.add(rejected(support,"negative fallback","size",sizeTypes,"java.lang.IllegalArgumentException",new String[]{},-1));
        rejectedRecords.add(rejected(support,"negative value","size",sizeTypes,"java.lang.IllegalArgumentException",new String[]{"-1"},42));
        rejectedRecords.add(rejected(support,"two arguments","size",sizeTypes,"java.lang.IllegalArgumentException",new String[]{"1","2"},42));
        for (String value : List.of("2147483648",""," 1","1 "))
          rejectedRecords.add(rejected(support,"integer:"+value,"size",sizeTypes,"java.lang.NumberFormatException",new String[]{value},42));
        report.put("integer_rejected",rejectedRecords);

        Class<?>[] fixedTypes = {double.class,int.class};
        List<String> vectors = Files.readAllLines(Path.of(args[2]),StandardCharsets.UTF_8);
        require(vectors.size()==1536,"Formatting vector inventory mismatch");
        int count=0;
        for (String line : vectors) {
          String[] fields=line.split("\t",-1); require(fields.length==3,"Malformed format vector");
          double value=Double.longBitsToDouble(Long.parseUnsignedLong(fields[0],16));
          int digits=Integer.parseInt(fields[1]);
          Object actual=call(support,"fixed",fixedTypes,value,digits);
          require(actual.equals(fields[2]),"Format mismatch at vector "+count+": "+actual+" != "+fields[2]);
          count++;
        }
        report.put("format_vectors",count);
        List<Object> formatRejections = new ArrayList<>();
        for (double value : new double[]{Double.NaN,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY})
          formatRejections.add(rejected(support,"nonfinite:"+value,"fixed",fixedTypes,"java.lang.IllegalArgumentException",value,9));
        for (int digits : new int[]{-1,19})
          formatRejections.add(rejected(support,"precision:"+digits,"fixed",fixedTypes,"java.lang.IllegalArgumentException",1.0,digits));
        report.put("format_rejected",formatRejections);

        String[] lineInputs={"","\n","\r\n","\r","a\r\nb\rc\n","\n\r\n\r","a","\u00ff\u0000\r\nb"};
        List<List<String>> lineExpected=List.of(List.of(""),List.of("",""),List.of("",""),List.of("",""),
          List.of("a","b","c",""),List.of("","","",""),List.of("a"),List.of("\u00ff\u0000","b"));
        List<Object> lineRecords=new ArrayList<>();
        for(int i=0;i<lineInputs.length;i++) {
          Object actual=call(support,"lines",new Class<?>[]{byte[].class},lineInputs[i].getBytes(StandardCharsets.ISO_8859_1));
          require(actual.equals(lineExpected.get(i)),"Line normalization mismatch at case "+i);
          lineRecords.add(Map.of("input",lineInputs[i],"lines",actual));
        }
        report.put("line_cases",lineRecords);

        byte[] input=(byte[])call(support,"input",new Class<?>[]{});
        require(input.length>2*65536,"Stdin must exceed two full input blocks");
        require(((byte[])call(support,"input",new Class<?>[]{})).length==0,"Repeated EOF was not empty");
        String text=(String)call(support,"text",new Class<?>[]{byte[].class},input);
        require(text.length()==input.length,"ISO-8859-1 length mismatch");
        boolean[] seen=new boolean[256];
        for(int i=0;i<input.length;i++) {
          int value=Byte.toUnsignedInt(input[i]);
          require(text.charAt(i)==value,"ISO-8859-1 character mismatch at "+i);
          seen[value]=true;
        }
        for(boolean value:seen)require(value,"Input omits a byte value");
        byte[] bytes=(byte[])call(support,"bytes",new Class<?>[]{String.class},text);
        require(Arrays.equals(bytes,input),"Byte/text round trip differs");
        call(support,"write",new Class<?>[]{byte[].class},input);
        call(support,"write",new Class<?>[]{String.class},text);
        report.put("input_bytes",input.length); report.put("repeated_eof",true);
        report.put("byte_values_verified",256); report.put("write_overloads_verified",2);
        report.put("non_platform_class_origins",loader.origins);
        report.put("main_loaded",false); report.put("status","passed");
      } catch (Throwable error) {
        report.put("error_type",error.getClass().getName()); report.put("error",error.getMessage());
        report.put("non_platform_class_origins",loader.origins);
        throw error;
      } finally {
        Files.writeString(summary,json(report)+"\n",StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
      }
    }
  }
}
