package sourcequalification;

import com.intellij.openapi.Disposable;
import com.intellij.openapi.util.Disposer;
import com.intellij.openapi.util.TextRange;
import com.intellij.psi.PsiComment;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiErrorElement;
import com.intellij.psi.PsiWhiteSpace;
import java.lang.management.ManagementFactory;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.jetbrains.kotlin.cli.jvm.compiler.EnvironmentConfigFiles;
import org.jetbrains.kotlin.cli.jvm.compiler.KotlinCoreEnvironment;
import org.jetbrains.kotlin.config.CompilerConfiguration;
import org.jetbrains.kotlin.psi.KtFile;
import org.jetbrains.kotlin.psi.KtPsiFactory;

/** Inspects retained source text with Kotlin PSI; never analyzes or compiles it. */
public final class SourceReader {
  static void require(boolean value, String message) {
    if (!value) throw new AssertionError(message);
  }

  static String sha(byte[] bytes) throws Exception {
    byte[] digest = MessageDigest.getInstance("SHA-256").digest(bytes);
    StringBuilder out = new StringBuilder();
    for (byte value : digest) out.append(String.format("%02x", value & 255));
    return out.toString();
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
      List<String> parts = new ArrayList<>();
      for (Map.Entry<?,?> entry : ((Map<?,?>)value).entrySet())
        parts.add(json(entry.getKey().toString()) + ":" + json(entry.getValue()));
      return "{" + String.join(",", parts) + "}";
    }
    if (value instanceof Iterable<?>) {
      List<String> parts = new ArrayList<>();
      for (Object item : (Iterable<?>)value) parts.add(json(item));
      return "[" + String.join(",", parts) + "]";
    }
    throw new AssertionError("Unsupported JSON value: " + value.getClass());
  }

  static void writeJson(Path path, Object value) throws Exception {
    Files.writeString(path, json(value) + "\n", StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
  }

  static int walk(PsiElement element, int parent, String source,
                  List<Map<String,Object>> nodes, List<Map<String,Object>> errors,
                  List<Map<String,Object>> leaves) {
    TextRange range = element.getTextRange();
    int start = range.getStartOffset(), end = range.getEndOffset();
    require(start >= 0 && end >= start && end <= source.length(), "PSI range outside source");
    require(source.substring(start, end).equals(element.getText()), "PSI text/range differs");
    int id = nodes.size();
    Map<String,Object> row = new LinkedHashMap<>();
    row.put("id", id); row.put("parent", parent);
    row.put("start_utf16", start); row.put("end_utf16", end);
    row.put("psi_class", element.getClass().getName());
    row.put("element_type", element.getNode().getElementType().toString());
    row.put("comment", element instanceof PsiComment);
    row.put("whitespace", element instanceof PsiWhiteSpace);
    List<Integer> children = new ArrayList<>(); row.put("children", children);
    nodes.add(row);
    if (element instanceof PsiErrorElement) {
      Map<String,Object> error = new LinkedHashMap<>();
      error.put("node", id); error.put("start_utf16", start); error.put("end_utf16", end);
      error.put("message", ((PsiErrorElement)element).getErrorDescription());
      errors.add(error);
    }
    for (PsiElement child = element.getFirstChild(); child != null; child = child.getNextSibling())
      children.add(walk(child, id, source, nodes, errors, leaves));
    if (children.isEmpty()) {
      row.put("text", element.getText()); leaves.add(row);
    }
    return id;
  }

  static Map<String,Object> inspect(KtPsiFactory factory, String[] entry, Path output) throws Exception {
    require(entry.length == 4 && entry[0].matches("[a-z0-9-]+") &&
            entry[2].matches("[0-9a-f]{64}") && (entry[3].equals("ok") || entry[3].equals("error")),
            "Malformed reader manifest entry");
    String id = entry[0];
    Path sourcePath = Path.of(new String(Base64.getDecoder().decode(entry[1]), StandardCharsets.UTF_8));
    byte[] raw = Files.readAllBytes(sourcePath);
    require(sha(raw).equals(entry[2]), "Retained source bytes changed: " + id);
    String source = StandardCharsets.UTF_8.newDecoder().decode(ByteBuffer.wrap(raw)).toString();
    KtFile file = factory.createFile(sourcePath.getFileName().toString(), source);
    String parsed = file.getText();
    String normalized = source.replace("\r\n", "\n").replace('\r', '\n');
    require(parsed.equals(source) || parsed.equals(normalized), "PSI changed source beyond newline normalization");
    Path directory = output.resolve(id); Files.createDirectory(directory);
    Files.write(directory.resolve("source.kt"), raw, StandardOpenOption.CREATE_NEW);
    Files.writeString(directory.resolve("psi-source.kt"), parsed, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
    List<Map<String,Object>> nodes = new ArrayList<>(), errors = new ArrayList<>(), leaves = new ArrayList<>();
    walk(file, -1, parsed, nodes, errors, leaves);
    int cursor = 0;
    for (Map<String,Object> leaf : leaves) {
      require((Integer)leaf.get("start_utf16") == cursor, "PSI leaves do not cover source exactly once");
      cursor = (Integer)leaf.get("end_utf16");
    }
    require(cursor == parsed.length(), "PSI leaves omit source suffix");
    Map<String,Object> evidence = new LinkedHashMap<>();
    evidence.put("schema", "kotlin-native-psi-source-v1"); evidence.put("id", id);
    evidence.put("source_path", sourcePath.toString()); evidence.put("source_sha256", sha(raw));
    evidence.put("psi_source_sha256", sha(parsed.getBytes(StandardCharsets.UTF_8)));
    evidence.put("offset_units", "UTF-16 code units"); evidence.put("source_utf16_length", parsed.length());
    evidence.put("newline_normalization_observed", !parsed.equals(source));
    evidence.put("nodes", nodes); evidence.put("parse_errors", errors);
    evidence.put("leaf_coverage_complete", true);
    writeJson(directory.resolve("psi.json"), evidence);
    require(entry[3].equals("ok") == errors.isEmpty(), "Unexpected Kotlin parser outcome: " + id);
    Map<String,Object> result = new LinkedHashMap<>();
    result.put("id", id); result.put("source_sha256", sha(raw));
    result.put("psi_source_sha256", evidence.get("psi_source_sha256"));
    result.put("psi_sha256", sha(Files.readAllBytes(directory.resolve("psi.json"))));
    result.put("status", errors.isEmpty() ? "parsed" : "expected-parse-rejection");
    result.put("nodes", nodes.size()); result.put("parse_errors", errors.size());
    result.put("canonical_loc", null); result.put("formatted_loc", null);
    return result;
  }

  public static void main(String[] args) throws Exception {
    require(args.length == 2, "Expected manifest TSV and new reader output directory");
    Path manifest = Path.of(args[0]), output = Path.of(args[1]);
    require(!Files.exists(output), "Fresh reader output required");
    Files.createDirectory(output);
    try {
      Class.forName("clbg.Support", false, SourceReader.class.getClassLoader());
      throw new AssertionError("Application classes must not be on the reader class path");
    } catch (ClassNotFoundException expected) {
      // Subject sources remain text, never classpath inputs.
    }
    Map<String,Object> runtime = new LinkedHashMap<>();
    runtime.put("java_home", System.getProperty("java.home"));
    runtime.put("runtime_version", System.getProperty("java.runtime.version"));
    runtime.put("class_path", System.getProperty("java.class.path"));
    runtime.put("flags", ManagementFactory.getRuntimeMXBean().getInputArguments());
    runtime.put("headless", System.getProperty("java.awt.headless"));
    runtime.put("application_class_canary", "clbg.Support unavailable");
    runtime.put("compiler_version", KotlinCoreEnvironment.class.getPackage().getImplementationVersion());
    Map<String,String> origins = new LinkedHashMap<>();
    for (Class<?> type : List.of(SourceReader.class, KotlinCoreEnvironment.class, KtPsiFactory.class,
                                CompilerConfiguration.class, Disposer.class, kotlin.Unit.class))
      origins.put(type.getName(), type.getProtectionDomain().getCodeSource().getLocation().toExternalForm());
    runtime.put("class_origins", origins);
    writeJson(output.resolve("started.json"), runtime);
    Disposable disposable = Disposer.newDisposable("benchmark-source-reader");
    List<Map<String,Object>> items = new ArrayList<>();
    try {
      KotlinCoreEnvironment environment = KotlinCoreEnvironment.createForProduction(disposable,
          new CompilerConfiguration(), EnvironmentConfigFiles.JVM_CONFIG_FILES);
      KtPsiFactory factory = new KtPsiFactory(environment.getProject(), false);
      for (String line : Files.readAllLines(manifest, StandardCharsets.UTF_8))
        items.add(inspect(factory, line.split("\t", -1), output));
    } finally {
      Disposer.dispose(disposable);
    }
    Map<String,Object> report = new LinkedHashMap<>();
    report.put("schema", "kotlin-native-source-reader-v1");
    report.put("status", "read-awaiting-canonical-owner-review");
    report.put("runtime", runtime); report.put("items", items);
    report.put("source_evaluations", 0); report.put("subject_recompilations", 0);
    report.put("subject_main_invocations", 0); report.put("canonical_loc", null);
    report.put("formatted_loc", null); report.put("chart_admission", false);
    writeJson(output.resolve("report.json"), report);
  }
}
